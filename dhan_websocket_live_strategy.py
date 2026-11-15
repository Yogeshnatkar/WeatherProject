"""
Dhan WebSocket live-candle scanner  (patched / hardened version)
----------------------------------------------------------------
UNCHANGED strategy logic (same as the uploaded version):
  - Indicator formulas in add_indicators()
  - BUY / SELL signal conditions
  - Signal cooldown (SIGNAL_COOLDOWN bars) and one-entry-per-candle rule
  - Exit rule: BUY exits when current 5m Close < previous 5m Open,
               SELL exits when current 5m Close > previous 5m Open
  - Quantity slabs

FIXES in this version:
  1. Tick time: candles are bucketed by wall-clock receive time by default
     (Dhan's LTT is a bare "HH:MM:SS" string whose timezone is ambiguous).
     Optional LTT use is guarded by a drift check.
  2. Performance: signal evaluation is throttled per symbol, runs in worker
     threads (not inside the SDK receive loop), uses a tail window of history,
     and the day-volume offset is maintained incrementally.
  3. Session filter: ticks outside 09:15-15:30 IST are ignored, new entries
     stop at ENTRY_CUTOFF, and everything open is squared off at
     SQUARE_OFF_TIME (a watchdog thread does this even if ticks stop).
     Optional ATR SL/TP exists but is OFF by default (USE_ATR_SL_TP=False),
     so the exit logic stays exactly as uploaded.
  4. Historical/5m API calls use full datetime strings, with retry/backoff
     on 429/5xx. Startup prints sanity warnings about timestamps.
  5. Thread safety: open_positions / totals / closed_trades are accessed
     under a lock. Exit checks cannot overlap per symbol and retry shortly
     if the REST candle is not published yet.
  6. No stacked positions in the same symbol (ALLOW_STACKING=False).
  7. Exit price/time use the live LTP/now at the moment the exit fires.

IMPORTANT:
  - Set credentials via environment variables only.
  - Keep PAPER_MODE=True until you have verified signals and fills.
  - Needs dhan_symbols.py with DHAN_SYMBOLS:
      {"SYMBOL": {"security_id": "...", "exchange_segment": "NSE_EQ",
                  "instrument": "EQUITY"}}
  - Intrabar signals can reverse before the 15-minute candle closes.
"""

import os
import time
import json
import threading
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import numpy as np
import pandas as pd
import requests
from zoneinfo import ZoneInfo

from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator

from dhanhq import DhanContext, MarketFeed

import dhan_symbols


# ============================================================
# CONFIGURATION
# ============================================================

IST = ZoneInfo("Asia/Kolkata")
UTC = dt.timezone.utc
DT_FMT = "%Y-%m-%d %H:%M:%S"

CANDLE_MINUTES = 15
EXIT_CANDLE_MINUTES = 5
HISTORY_DAYS = 70

EMA_FAST = 20
EMA_SLOW = 50
EMA_REGIME = 200

VOLUME_MULTIPLIER = 1
ROLLING_SWING = 20
ATR_PERIOD = 14

TP_ATR_MULT = 2.5
SL_ATR_MULT = 1.0

RSI_LONG_MIN = 40
RSI_LONG_MAX = 70
RSI_SHORT_MIN = 30
RSI_SHORT_MAX = 60

BODY_RATIO_MIN = 0.30
SIGNAL_COOLDOWN = 3

# ---- Session control (IST) ----
SESSION_START = dt.time(9, 15)
SESSION_END = dt.time(15, 30)
ENTRY_CUTOFF = dt.time(15, 0)        # no new entries at/after this; None = off
SQUARE_OFF_TIME = dt.time(15, 15)    # force-exit everything at/after this

# ---- Tick time handling ----
# False (recommended): bucket candles by wall-clock receive time.
# True: try Dhan's LTT, but only if it lands within MAX_TICK_DRIFT_SECONDS of
#       the wall clock under an IST or UTC interpretation; else use wall clock.
USE_EXCHANGE_LTT = False
MAX_TICK_DRIFT_SECONDS = 120

# ---- Performance ----
SIGNAL_EVAL_INTERVAL = 0.43          # min seconds between evaluations / symbol
INDICATOR_TAIL_ROWS = 600            # history rows used for indicators
WORKERS_SIGNAL = 4

# ---- Exits ----
EXIT_RETRY_SECONDS = 20              # retry if 5m REST candles not ready yet
ALLOW_STACKING = False               # False = max 1 open position per symbol
USE_ATR_SL_TP = False                # OFF = exit logic identical to upload

# ---- API robustness ----
API_RETRIES = 3
WARMUP_PAUSE_SECONDS = 0.25

# Keep True until paper testing is complete.
PAPER_MODE = True
ENABLE_SANDBOX_ORDERS = False

DHAN_CLIENT_ID = dhan_symbols.DHAN_CLIENT_ID
DHAN_ACCESS_TOKEN = dhan_symbols.DHAN_ACCESS_TOKEN

DHAN_SANDBOX_CLIENT_ID = dhan_symbols.DHAN_Sandbox_ClientId
DHAN_SANDBOX_ACCESS_TOKEN = dhan_symbols.DHAN_Sandbox_ACCESS_TOKEN
TELEGRAM_BOT_TOKEN = dhan_symbols.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = dhan_symbols.TELEGRAM_CHAT_ID

DHAN_SYMBOLS = dhan_symbols.DHAN_SYMBOLS
# DHAN_SYMBOLS = dhan_symbols.commodity

DHAN_INTRADAY_URL = "https://api.dhan.co/v2/charts/intraday"
DHAN_SANDBOX_ORDER_URL = "https://sandbox.dhan.co/v2/orders"

FEED_MODE = MarketFeed.Quote

TELEGRAM_EXECUTOR = ThreadPoolExecutor(max_workers=4)
ORDER_EXECUTOR = ThreadPoolExecutor(max_workers=4)
EXIT_EXECUTOR = ThreadPoolExecutor(max_workers=4)
SIGNAL_EXECUTOR = ThreadPoolExecutor(max_workers=WORKERS_SIGNAL)

# ============================================================
# STATE
# ============================================================

state_lock = threading.RLock()
log_lock = threading.Lock()

market_frames: dict[str, pd.DataFrame] = {}
forming_candles: dict[str, dict] = {}

# Incremental "volume of completed candles today" per symbol.
completed_vol: dict[str, float] = {}
completed_vol_date: dict[str, dt.date] = {}

last_signal_candle: dict[str, pd.Timestamp] = {}
acted_signal_candles: dict[str, set[str]] = {}

# Signal evaluation throttling
eval_inflight: set[str] = set()
last_eval_mono: dict[str, float] = {}
last_eval_sig: dict[str, tuple] = {}

# Exit polling
last_exit_bucket: dict[str, pd.Timestamp] = {}
exit_inflight: set[str] = set()
exit_retry_at: dict[str, float] = {}

open_positions: dict[str, dict] = {}
closed_trades: list[dict] = []
total_pnl_rs = 0.0
total_invested_rs = 0.0

ltt_fallback_count = 0

SECURITY_TO_SYMBOL: dict[str, str] = {
    str(info["security_id"]): symbol
    for symbol, info in DHAN_SYMBOLS.items()
}

# ============================================================
# GENERAL HELPERS
# ============================================================

def get_ist_now() -> dt.datetime:
    return dt.datetime.now(IST)


def as_ist_timestamp(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize(IST)
    return ts.tz_convert(IST)


def floor_time(ts: pd.Timestamp, minutes: int) -> pd.Timestamp:
    ts = as_ist_timestamp(ts)
    minute_of_day = ts.hour * 60 + ts.minute
    floored = (minute_of_day // minutes) * minutes
    hour, minute = divmod(floored, 60)
    return ts.normalize() + pd.Timedelta(hours=hour, minutes=minute)


def in_session(ts) -> bool:
    t = as_ist_timestamp(ts).time()
    return SESSION_START <= t < SESSION_END


def entry_allowed(ts) -> bool:
    if not in_session(ts):
        return False
    t = as_ist_timestamp(ts).time()
    if t >= SQUARE_OFF_TIME:
        return False
    if ENTRY_CUTOFF is not None and t >= ENTRY_CUTOFF:
        return False
    return True


def create_beep_sound() -> None:
    print("\a", end="", flush=True)
    print("🔔 LIVE SIGNAL")


def send_telegram_message(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=8,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[TELEGRAM ERROR] {exc}")


def send_telegram_background(message: str) -> None:
    TELEGRAM_EXECUTOR.submit(send_telegram_message, message)


def write_trade_log(message: str) -> None:
    with log_lock:
        with open(f"trade_log_{dt.datetime.now().strftime('%Y-%m-%d')}.txt", "a", encoding="utf-8") as file:
            file.write(message + "\n\n")


def get_quantity(price: float) -> int:
    # Same quantity slabs as the uploaded code.
    if price < 1000:
        return 400
    elif price < 3000:
        return 100
    return 25




def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    required = ["Datetime", "Open", "High", "Low", "Close", "Volume"]
    if df.empty:
        return pd.DataFrame(columns=required)

    out = df.copy()
    out["Datetime"] = pd.to_datetime(out["Datetime"])
    if out["Datetime"].dt.tz is None:
        out["Datetime"] = out["Datetime"].dt.tz_localize("UTC").dt.tz_convert(IST)
    else:
        out["Datetime"] = out["Datetime"].dt.tz_convert(IST)

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.dropna(subset=required)
    out = out.drop_duplicates("Datetime", keep="last")
    return out.sort_values("Datetime").reset_index(drop=True)


def dhan_headers() -> dict:
    return {
        "access-token": DHAN_ACCESS_TOKEN,
        "client-id": DHAN_CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def post_with_retry(url: str, payload: dict, timeout: int) -> dict:
    """POST with retry/backoff on 429 / 5xx / network errors."""
    last_exc: Optional[Exception] = None
    for attempt in range(1, API_RETRIES + 1):
        try:
            response = requests.post(
                url, headers=dhan_headers(), json=payload, timeout=timeout
            )
            if response.status_code == 429 or response.status_code >= 500:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_exc = exc
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"API failed after {API_RETRIES} attempts: {last_exc}")


# ============================================================
# TICK TIME RESOLUTION
# ============================================================

def resolve_tick_time(ltt, now: dt.datetime) -> dt.datetime:
    """
    Dhan SDK gives LTT as a bare 'HH:MM:SS' string. Its timezone is ambiguous,
    so only trust it if it matches the wall clock under IST or UTC reading.
    Otherwise use the wall clock.
    """
    global ltt_fallback_count
    try:
        if isinstance(ltt, str) and ltt.count(":") == 2:
            h, m, s = (int(x) for x in ltt.split(":"))
            base = now.date()
            as_ist = dt.datetime(base.year, base.month, base.day, h, m, s, tzinfo=IST)
            as_utc = dt.datetime(
                base.year, base.month, base.day, h, m, s, tzinfo=UTC
            ).astimezone(IST)
            for cand in (as_ist, as_utc):
                if abs((cand - now).total_seconds()) <= MAX_TICK_DRIFT_SECONDS:
                    return cand
    except Exception:
        pass

    ltt_fallback_count += 1
    if ltt_fallback_count % 500 == 1:
        print(
            f"[LTT] Using wall-clock time (LTT={ltt!r} did not match clock; "
            f"count={ltt_fallback_count})"
        )
    return now


# ============================================================
# HISTORICAL WARM-UP
# ============================================================

def download_dhan_history(symbol: str, period_days: int = HISTORY_DAYS) -> pd.DataFrame:
    """REST history used once at startup to seed EMA200 / RSI / ATR / swings."""
    if symbol not in DHAN_SYMBOLS:
        raise ValueError(f"{symbol} missing from DHAN_SYMBOLS")

    info = DHAN_SYMBOLS[symbol]
    end_dt = get_ist_now()
    start_dt = (end_dt - dt.timedelta(days=period_days)).replace(
        hour=9, minute=15, second=0, microsecond=0
    )

    payload = {
        "securityId": str(info["security_id"]),
        "exchangeSegment": info.get("exchange_segment", "NSE_EQ"),
        "instrument": info.get("instrument", "EQUITY"),
        "interval": str(CANDLE_MINUTES),
        "oi": False,
        "fromDate": start_dt.strftime(DT_FMT),
        "toDate": end_dt.strftime(DT_FMT),
    }

    data = post_with_retry(DHAN_INTRADAY_URL, payload, timeout=30)

    keys = ("open", "high", "low", "close", "volume", "timestamp")
    if not all(k in data for k in keys):
        raise RuntimeError(f"Unexpected historical response for {symbol}: {data}")

    if not data["timestamp"]:
        return pd.DataFrame(
            columns=["Datetime", "Open", "High", "Low", "Close", "Volume"]
        )

    df = pd.DataFrame({
        "Datetime": pd.to_datetime(
            data["timestamp"], unit="s", utc=True
        ).tz_convert(IST),
        "Open": data["open"],
        "High": data["high"],
        "Low": data["low"],
        "Close": data["close"],
        "Volume": data["volume"],
    })
    return normalize_history(df)


def initialize_symbol_history(symbol: str) -> None:
    history = download_dhan_history(symbol)

    if history.empty:
        raise RuntimeError(f"No historical candles received for {symbol}")

    now = get_ist_now()
    now_ts = pd.Timestamp(now)
    current_bucket = floor_time(now_ts, CANDLE_MINUTES)

    # Sanity check 1: timestamps in the future => timezone/epoch offset issue.
    last_ts = as_ist_timestamp(history["Datetime"].iloc[-1])
    if last_ts > now_ts + pd.Timedelta(minutes=CANDLE_MINUTES):
        print(
            f"[WARN] {symbol}: last historical candle {last_ts} is in the future "
            f"(now={now:%H:%M:%S}). Check the timestamp timezone from Dhan."
        )

    candle_starts = history["Datetime"].map(
        lambda x: floor_time(pd.Timestamp(x), CANDLE_MINUTES)
    )
    same_bucket = candle_starts == current_bucket

    current_seed = None
    if same_bucket.any():
        current_seed = history.loc[same_bucket].iloc[-1].to_dict()
        history = history.loc[~same_bucket].copy()

    history = history.reset_index(drop=True)
    market_frames[symbol] = history

    # Incremental completed-volume-today offset.
    today = now.date()
    dates = history["Datetime"].dt.date
    completed_vol[symbol] = float(history.loc[dates == today, "Volume"].sum())
    completed_vol_date[symbol] = today

    # Sanity check 2: during session, today's candles must be present.
    if in_session(now) and now.time() > dt.time(9, 35):
        if completed_vol[symbol] == 0.0 and current_seed is None:
            print(
                f"[WARN] {symbol}: no candles for today in history. Live volume "
                f"will be overstated until the next candle closes."
            )

    if current_seed is not None:
        forming_candles[symbol] = {
            "bucket": current_bucket,
            "Open": float(current_seed["Open"]),
            "High": float(current_seed["High"]),
            "Low": float(current_seed["Low"]),
            "Close": float(current_seed["Close"]),
            "Volume": float(current_seed["Volume"]),
            "seed_volume": float(current_seed["Volume"]),
            "last_ltp": float(current_seed["Close"]),
        }
    else:
        forming_candles[symbol] = {
            "bucket": current_bucket,
            "Open": None,
            "High": None,
            "Low": None,
            "Close": None,
            "Volume": 0.0,
            "seed_volume": 0.0,
            "last_ltp": None,
        }

    acted_signal_candles.setdefault(symbol, set())
    print(
        f"[WARMUP] {symbol}: {len(history)} completed candles; "
        f"last={last_ts:%Y-%m-%d %H:%M}; forming candle={current_bucket}"
    )


def warm_up_all_symbols() -> None:
    if not DHAN_CLIENT_ID or not DHAN_ACCESS_TOKEN:
        raise RuntimeError(
            "Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN environment variables."
        )

    for symbol in DHAN_SYMBOLS:
        try:
            initialize_symbol_history(symbol)
        except Exception as exc:
            print(f"[WARMUP ERROR] {symbol}: {exc}")
        time.sleep(WARMUP_PAUSE_SECONDS)


# ============================================================
# INDICATORS AND ORIGINAL SIGNAL LOGIC  (UNCHANGED)
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Indicator formulas retained from the uploaded function.
    body_long/body_short are calculated but intentionally NOT part of the
    active BUY/SELL conditions (same as the upload).
    """
    df = df.copy()

    df["EMA20"] = EMAIndicator(df["Close"], window=EMA_FAST).ema_indicator()
    df["EMA50"] = EMAIndicator(df["Close"], window=EMA_SLOW).ema_indicator()
    df["EMA200"] = EMAIndicator(df["Close"], window=EMA_REGIME).ema_indicator()

    df["vol_ma20"] = df["Volume"].rolling(20, min_periods=1).mean()

    atr = AverageTrueRange(
        df["High"], df["Low"], df["Close"], window=ATR_PERIOD
    )
    df["ATR14"] = atr.average_true_range()
    df["ATR14_MA20"] = df["ATR14"].rolling(20).mean()

    df["prev_high"] = df["High"].shift(1).rolling(ROLLING_SWING).max()
    df["prev_low"] = df["Low"].shift(1).rolling(ROLLING_SWING).min()

    df["sweep_long"] = (
        (df["Low"] < df["prev_low"]) &
        (df["Close"] > df["prev_low"])
    )
    df["sweep_short"] = (
        (df["High"] > df["prev_high"]) &
        (df["Close"] < df["prev_high"])
    )

    df["trend_long"] = (
        (df["EMA20"] > df["EMA50"]) &
        (df["Close"] > df["EMA200"])
    )
    df["trend_short"] = (
        (df["EMA20"] < df["EMA50"]) &
        (df["Close"] < df["EMA200"])
    )

    df["vol_confirm"] = (
        df["Volume"] > (VOLUME_MULTIPLIER * df["vol_ma20"])
    )

    df["atr_confirm"] = df["ATR14"] > df["ATR14_MA20"]

    df["RSI14"] = RSIIndicator(df["Close"], window=14).rsi()
    df["rsi_long"] = (
        (df["RSI14"] > RSI_LONG_MIN) &
        (df["RSI14"] < RSI_LONG_MAX)
    )
    df["rsi_short"] = (
        (df["RSI14"] < RSI_SHORT_MAX) &
        (df["RSI14"] > RSI_SHORT_MIN)
    )

    candle_range = (df["High"] - df["Low"]).replace(0, np.nan)
    df["body_long"] = (
        (df["Close"] - df["Open"]) / candle_range > BODY_RATIO_MIN
    )
    df["body_short"] = (
        (df["Open"] - df["Close"]) / candle_range > BODY_RATIO_MIN
    )

    df["BUY_SIGNAL"] = (
        df["sweep_long"]
        & df["trend_long"]
        & df["atr_confirm"]
        & df["rsi_long"]
        & df["vol_confirm"]
        & df["body_long"]
    )

    df["SELL_SIGNAL"] = (
        df["sweep_short"]
        & df["trend_short"]
        & df["atr_confirm"]
        & df["rsi_short"]
        & df["vol_confirm"]
        & df["body_short"]
    )

    return df


def cooldown_allows(symbol: str, candle_bucket: pd.Timestamp) -> bool:
    previous = last_signal_candle.get(symbol)
    if previous is None:
        return True

    elapsed_seconds = (candle_bucket - previous).total_seconds()
    elapsed_bars = elapsed_seconds / (CANDLE_MINUTES * 60)
    return elapsed_bars >= SIGNAL_COOLDOWN


def symbol_has_open_position(symbol: str) -> bool:
    with state_lock:
        return any(p["symbol"] == symbol for p in open_positions.values())


def process_live_signal(symbol: str) -> None:
    """
    Recalculates the unchanged strategy on the latest live candle.
    Heavy pandas work happens outside the lock on a snapshot; the decision
    to act (dedupe / cooldown / mark) is made atomically under the lock.
    """
    now = get_ist_now()
    if not entry_allowed(now):
        return

    # ---- snapshot under lock ----
    with state_lock:
        hist = market_frames.get(symbol)
        forming = forming_candles.get(symbol)

        if hist is None or forming is None or forming["Open"] is None:
            return

        current_row = {
            "Datetime": forming["bucket"],
            "Open": forming["Open"],
            "High": forming["High"],
            "Low": forming["Low"],
            "Close": forming["Close"],
            "Volume": forming["Volume"],
        }
        hist_tail = hist.tail(INDICATOR_TAIL_ROWS)
        # hist_tail = hist.copy()
        live_price = float(forming["Close"])

    # ---- heavy compute outside lock ----
    combined = pd.concat(
        [hist_tail, pd.DataFrame([current_row])],
        ignore_index=True,
    )
    combined = combined.drop_duplicates("Datetime", keep="last").reset_index(drop=True)

    if len(combined) < max(EMA_REGIME, ROLLING_SWING, ATR_PERIOD) + 20:
        return

    calculated = add_indicators(combined)
    latest = calculated.iloc[-1]

    candle_bucket = as_ist_timestamp(latest["Datetime"])
    candle_key = f"{candle_bucket.isoformat()}"

    buy = bool(latest["BUY_SIGNAL"]) if pd.notna(latest["BUY_SIGNAL"]) else False
    sell = bool(latest["SELL_SIGNAL"]) if pd.notna(latest["SELL_SIGNAL"]) else False

    if not (buy or sell):
        return

    # ---- decide atomically ----
    with state_lock:
        if candle_key in acted_signal_candles.setdefault(symbol, set()):
            return

        if not cooldown_allows(symbol, candle_bucket):
            return

        if not ALLOW_STACKING and symbol_has_open_position(symbol):
            return

        acted_signal_candles[symbol].add(candle_key)
        last_signal_candle[symbol] = candle_bucket

    side = "BUY" if buy else "SELL"
    signal_time = get_ist_now()
    entry_price = live_price
    entry_atr = float(latest["ATR14"]) if pd.notna(latest["ATR14"]) else None

    create_beep_sound()

    msg = (
        f"📡 LIVE {side} SIGNAL\n"
        f"Symbol       : {symbol}\n"
        f"Candle Start : {candle_bucket}\n"
        f"Signal Time  : {signal_time:%Y-%m-%d %H:%M:%S %Z}\n"
        f"Live LTP     : ₹{entry_price:.2f}\n"
        f"RSI          : {latest['RSI14']:.2f}\n"
        f"ATR          : {latest['ATR14']:.2f}\n"
        f"Volume       : {latest['Volume']:.0f}\n"
        f"Volume MA20  : {latest['vol_ma20']:.0f}"
    )
    print("\n" + msg)
    send_telegram_background(msg)

    enter_position(
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        entry_time=signal_time,
        candle_time=candle_bucket,
        entry_atr=entry_atr,
    )


def schedule_signal_eval(symbol: str) -> None:
    """Throttled, non-blocking evaluation (never runs inside the WS loop)."""
    now_m = time.monotonic()
    with state_lock:
        if symbol in eval_inflight:
            return
        if now_m - last_eval_mono.get(symbol, 0.0) < SIGNAL_EVAL_INTERVAL:
            return

        f = forming_candles.get(symbol)
        if f is None or f["Open"] is None:
            return

        sig = (f["High"], f["Low"], f["Close"], f["Volume"])
        if last_eval_sig.get(symbol) == sig:
            return

        last_eval_sig[symbol] = sig
        last_eval_mono[symbol] = now_m
        eval_inflight.add(symbol)

    SIGNAL_EXECUTOR.submit(_signal_worker, symbol)


def _signal_worker(symbol: str) -> None:
    try:
        process_live_signal(symbol)
    except Exception as exc:
        print(f"[SIGNAL ERROR] {symbol}: {exc}")
    finally:
        with state_lock:
            eval_inflight.discard(symbol)


# ============================================================
# LIVE 15-MINUTE CANDLE BUILDER
# ============================================================

def add_completed_volume(symbol: str, bucket: pd.Timestamp, volume: float) -> None:
    day = as_ist_timestamp(bucket).date()
    if completed_vol_date.get(symbol) != day:
        completed_vol_date[symbol] = day
        completed_vol[symbol] = 0.0
    completed_vol[symbol] += float(volume)


def update_live_candle(
    symbol: str,
    ltp: float,
    cumulative_day_volume: Optional[int],
    tick_time: dt.datetime,
) -> None:
    """
    Build OHLC from WebSocket LTP updates.
    Quote volume is cumulative day volume, so:
        candle volume = cumulative day volume - completed candle volume today
    (the completed-volume offset is maintained incrementally).
    """
    if ltp <= 0:
        return

    tick_ts = as_ist_timestamp(tick_time)
    bucket = floor_time(tick_ts, CANDLE_MINUTES)

    with state_lock:
        if symbol not in forming_candles:
            return

        state = forming_candles[symbol]

        # Tick belongs to a later candle: finalize the old one.
        if bucket > state["bucket"]:
            old_bucket = state["bucket"]

            if state["Open"] is not None:
                old_row = {
                    "Datetime": old_bucket,
                    "Open": state["Open"],
                    "High": state["High"],
                    "Low": state["Low"],
                    "Close": state["Close"],
                    "Volume": state["Volume"],
                }
                frame = pd.concat(
                    [market_frames[symbol], pd.DataFrame([old_row])],
                    ignore_index=True,
                )
                frame = normalize_history(frame)
                market_frames[symbol] = frame.tail(1500).reset_index(drop=True)
                # market_frames[symbol] = frame.reset_index(drop=True)
                add_completed_volume(symbol, old_bucket, state["Volume"])

            forming_candles[symbol] = {
                "bucket": bucket,
                "Open": float(ltp),
                "High": float(ltp),
                "Low": float(ltp),
                "Close": float(ltp),
                "Volume": 0.0,
                "seed_volume": 0.0,
                "last_ltp": float(ltp),
            }
            state = forming_candles[symbol]

        # Ignore late/out-of-order ticks from an older candle.
        if bucket < state["bucket"]:
            return

        if state["Open"] is None:
            state["Open"] = float(ltp)
            state["High"] = float(ltp)
            state["Low"] = float(ltp)
            state["Close"] = float(ltp)
            state["Volume"] = 0.0
            state["seed_volume"] = 0.0

        state["High"] = max(float(state["High"]), float(ltp))
        state["Low"] = min(float(state["Low"]), float(ltp))
        state["Close"] = float(ltp)
        state["last_ltp"] = float(ltp)

        if cumulative_day_volume is not None:
            today = tick_ts.date()
            completed = (
                completed_vol.get(symbol, 0.0)
                if completed_vol_date.get(symbol) == today
                else 0.0
            )
            derived_current_volume = max(0.0, float(cumulative_day_volume) - completed)
            state["Volume"] = max(
                float(state.get("seed_volume", 0.0)),
                derived_current_volume,
            )


def latest_price(symbol: str, fallback: float) -> float:
    with state_lock:
        f = forming_candles.get(symbol)
        if f and f.get("last_ltp"):
            return float(f["last_ltp"])
    return float(fallback)


# ============================================================
# POSITION MANAGEMENT
# ============================================================

def place_sandbox_order(
    transaction_type: str,
    symbol: str,
    quantity: int,
) -> dict:
    if not DHAN_SANDBOX_CLIENT_ID or not DHAN_SANDBOX_ACCESS_TOKEN:
        raise RuntimeError(
            "Set DHAN_SANDBOX_CLIENT_ID and DHAN_SANDBOX_ACCESS_TOKEN."
        )

    info = DHAN_SYMBOLS[symbol]
    payload = {
        "dhanClientId": DHAN_SANDBOX_CLIENT_ID,
        "transactionType": transaction_type.upper(),
        "exchangeSegment": info.get("exchange_segment", "NSE_EQ"),
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": str(info["security_id"]),
        "quantity": int(quantity),
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "access-token": DHAN_SANDBOX_ACCESS_TOKEN,
    }

    response = requests.post(
        DHAN_SANDBOX_ORDER_URL,
        json=payload,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def submit_order_background(side: str, symbol: str, quantity: int) -> None:
    def worker():
        try:
            result = place_sandbox_order(side, symbol, quantity)
            print(f"[SANDBOX ORDER RESPONSE] {symbol}: {result}")
        except Exception as exc:
            print(f"[SANDBOX ORDER ERROR] {symbol}: {exc}")

    ORDER_EXECUTOR.submit(worker)


def enter_position(
    symbol: str,
    side: str,
    entry_price: float,
    entry_time: dt.datetime,
    candle_time: Optional[pd.Timestamp] = None,
    entry_atr: Optional[float] = None,
) -> None:
    """
    Entry price/time are signal-time LTP/time, not a confirmed exchange fill.
    For live orders, replace with Dhan's trade-book fill details.
    """
    qty = get_quantity(entry_price)
    position_key = f"{symbol}_{entry_time.isoformat()}"

    position = {
        "symbol": symbol,
        "side": side,
        "entry_price": float(entry_price),
        "entry_time": entry_time,
        "candle_time": candle_time,
        "qty": qty,
        "entry_atr": entry_atr,
        "status": "PAPER" if PAPER_MODE else "PENDING",
    }

    with state_lock:
        open_positions[position_key] = position

    message = (
        f"ENTRY [{side}]\n"
        f"Symbol      : {symbol}\n"
        f"Candle Time : {candle_time}\n"
        f"Signal Time : {entry_time}\n"
        f"Signal LTP  : ₹{entry_price:.2f}\n"
        f"Qty         : {qty}\n"
        f"Value       : ₹{entry_price * qty:,.2f}\n"
        f"Mode        : {'PAPER' if PAPER_MODE else 'ORDER'}"
    )
    print(message)
    write_trade_log(message)

    if ENABLE_SANDBOX_ORDERS and not PAPER_MODE:
        submit_order_background(side, symbol, qty)


def exit_position(
    position_key: str,
    exit_price: float,
    exit_time: dt.datetime,
    reason: str = "RULE",
) -> None:
    global total_pnl_rs, total_invested_rs

    with state_lock:
        pos = open_positions.pop(position_key, None)
        if pos is None:
            return

        side = pos["side"]
        entry = float(pos["entry_price"])
        qty = int(pos["qty"])

        pnl_rs = (
            (exit_price - entry) * qty
            if side == "BUY"
            else (entry - exit_price) * qty
        )
        invested = entry * qty
        pnl_pct = (pnl_rs / invested) * 100 if invested else 0.0

        total_pnl_rs += pnl_rs
        total_invested_rs += invested
        total_pct = (
            (total_pnl_rs / total_invested_rs) * 100
            if total_invested_rs else 0.0
        )

        closed_trades.append({
            "symbol": pos["symbol"],
            "side": side,
            "qty": qty,
            "entry_time": pos["entry_time"],
            "entry_price": entry,
            "exit_time": exit_time,
            "exit_price": exit_price,
            "pnl_rs": pnl_rs,
            "pnl_pct": pnl_pct,
            "reason": reason,
        })
        closed_count = len(closed_trades)
        run_total_pnl = total_pnl_rs

    message = (
        f"EXIT [{side}] ({reason})\n"
        f"Symbol      : {pos['symbol']}\n"
        f"Entry       : ₹{entry:.2f} @ {pos['entry_time']}\n"
        f"Exit        : ₹{exit_price:.2f} @ {exit_time}\n"
        f"Qty         : {qty}\n"
        f"Trade P&L   : ₹{pnl_rs:,.2f} ({pnl_pct:+.2f}%)\n"
        f"Total P&L   : ₹{run_total_pnl:,.2f} ({total_pct:+.2f}%)\n"
        f"Closed      : {closed_count}"
    )
    print(message)
    write_trade_log(message)
    send_telegram_background(message)

    exit_side = "SELL" if side.upper() == "BUY" else "BUY"
    if ENABLE_SANDBOX_ORDERS and not PAPER_MODE:
        submit_order_background(exit_side, pos["symbol"], qty)


MAX_LOSS_PER_POSITION = 1200  # rupees

def check_sl_tp(symbol: str, ltp: float) -> None:
    with state_lock:
        positions = [
            (k, p) for k, p in open_positions.items() if p["symbol"] == symbol
        ]

    for key, pos in positions:
        entry = pos["entry_price"]
        qty = pos["qty"]
        side = pos["side"].upper()

        pnl = (ltp - entry) * qty if side == "BUY" else (entry - ltp) * qty

        # Hard rupee stop-loss: always active
        if pnl <= -MAX_LOSS_PER_POSITION:
            exit_position(key, ltp, get_ist_now(), "MAX LOSS SL")
            continue

        # Optional ATR SL/TP
        if not USE_ATR_SL_TP:
            continue
        atr = pos.get("entry_atr")
        if not atr:
            continue
        if side == "BUY":
            sl, tp = entry - SL_ATR_MULT * atr, entry + TP_ATR_MULT * atr
            reason = "SL" if ltp <= sl else "TP" if ltp >= tp else None
        else:
            sl, tp = entry + SL_ATR_MULT * atr, entry - TP_ATR_MULT * atr
            reason = "SL" if ltp >= sl else "TP" if ltp <= tp else None
        if reason:
            exit_position(key, ltp, get_ist_now(), reason)
            
            
def session_watchdog() -> None:
    """Squares off all open positions at SQUARE_OFF_TIME, even if ticks stop."""
    while True:
        time.sleep(5)
        try:
            now = get_ist_now()
            if now.time() < SQUARE_OFF_TIME:
                continue
            with state_lock:
                items = list(open_positions.items())
            for key, pos in items:
                price = latest_price(pos["symbol"], pos["entry_price"])
                exit_position(key, price, now, "EOD SQUARE-OFF")
        except Exception as exc:
            print(f"[WATCHDOG ERROR] {exc}")


# ============================================================
# EXISTING 5-MINUTE EXIT DATA / EXIT RULE  (logic UNCHANGED)
# ============================================================

def get_5min_candles(
    security_id: str,
    exchange_segment: str = "NSE_EQ",
    instrument_type: str = "EQUITY",
    start_date: Optional[dt.datetime] = None,
    end_date: Optional[dt.datetime] = None,
) -> pd.DataFrame:
    if start_date is None:
        start_date = get_ist_now()
    if end_date is None:
        end_date = get_ist_now()

    # From the start of the entry day so the candle containing the entry
    # (needed as "previous candle") is always included.
    from_dt = as_ist_timestamp(start_date).normalize().replace(hour=9, minute=0)

    payload = {
        "securityId": str(security_id),
        "exchangeSegment": exchange_segment,
        "instrument": instrument_type,
        "interval": "5",
        "oi": False,
        "fromDate": from_dt.strftime(DT_FMT),
        "toDate": as_ist_timestamp(end_date).strftime(DT_FMT),
    }

    data = post_with_retry(DHAN_INTRADAY_URL, payload, timeout=15)

    if not data.get("timestamp"):
        return pd.DataFrame(
            columns=["Datetime", "Open", "High", "Low", "Close", "Volume"]
        )

    df = pd.DataFrame({
        "Datetime": pd.to_datetime(
            data["timestamp"], unit="s", utc=True
        ).tz_convert(IST),
        "Open": data["open"],
        "High": data["high"],
        "Low": data["low"],
        "Close": data["close"],
        "Volume": data["volume"],
    })
    return normalize_history(df)


def check_exit_for_symbol(symbol: str, bucket) -> None:
    """
    Original exit condition preserved:
      BUY exits when current 5m Close < previous 5m Open
      SELL exits when current 5m Close > previous 5m Open
    """
    info = DHAN_SYMBOLS[symbol]
    with state_lock:
        positions = [
            (key, pos)
            for key, pos in open_positions.items()
            if pos["symbol"] == symbol
        ]
    if not positions:
        exit_retry_at.pop(symbol, None)
        return

    earliest_entry = min(pos["entry_time"] for _, pos in positions)

    try:
        candles = get_5min_candles(
            security_id=info["security_id"],
            exchange_segment=info.get("exchange_segment", "NSE_EQ"),
            instrument_type=info.get("instrument", "EQUITY"),
            start_date=earliest_entry,
            end_date=get_ist_now(),
        )
    except Exception as exc:
        print(f"[EXIT CHECK ERROR] {symbol}: {exc}")
        exit_retry_at[symbol] = time.monotonic() + EXIT_RETRY_SECONDS
        return

    if candles.empty:
        exit_retry_at[symbol] = time.monotonic() + EXIT_RETRY_SECONDS
        return

    candles = candles.sort_values("Datetime").reset_index(drop=True)

    # Keep only closed candles: those that start before the current bucket
    bucket_ts = as_ist_timestamp(bucket)
    candles = candles[
        candles["Datetime"].apply(as_ist_timestamp) < bucket_ts
    ].reset_index(drop=True)

    # The candle that just closed must be present, otherwise API is lagging
    expected_last = bucket_ts - pd.Timedelta(minutes=EXIT_CANDLE_MINUTES)
    have_expected = (
        not candles.empty
        and as_ist_timestamp(candles["Datetime"].iloc[-1]) >= expected_last
    )
    secs_since_bucket = (
        as_ist_timestamp(get_ist_now()) - bucket_ts
    ).total_seconds()

    if not have_expected and secs_since_bucket < 60:
        # API probably lagging: retry for up to ~60s after the boundary
        exit_retry_at[symbol] = time.monotonic() + EXIT_RETRY_SECONDS
        return

    exit_retry_at.pop(symbol, None)
    if len(candles) < 2:
        return

    for position_key, pos in positions:
        entry_ts = as_ist_timestamp(pos["entry_time"])

        for i in range(1, len(candles)):
            candle_time = as_ist_timestamp(candles.loc[i, "Datetime"])
            if candle_time <= entry_ts:
                continue

            curr_close = float(candles.loc[i, "Close"])
            # Uploaded logic compares against the previous candle's OPEN.
            prev_open = float(candles.loc[i - 1, "Open"])

            side = pos["side"].upper()
            should_exit = (
                side == "BUY" and curr_close < prev_open
            ) or (
                side == "SELL" and curr_close > prev_open
            )

            if should_exit:
                price = latest_price(symbol, curr_close)
                exit_position(position_key, price, get_ist_now(), "5m RULE")
                break


def _exit_worker(symbol: str, bucket) -> None:
    try:
        check_exit_for_symbol(symbol, bucket)
    except Exception as exc:
        print(f"[EXIT WORKER ERROR] {symbol}: {exc}")
    finally:
        with state_lock:
            exit_inflight.discard(symbol)
            missed = last_exit_bucket.get(symbol) != bucket
            if missed and any(p["symbol"] == symbol for p in open_positions.values()):
                exit_retry_at[symbol] = time.monotonic()  # retry on next tick


def maybe_check_exit(symbol: str, tick_time: dt.datetime) -> None:
    bucket = floor_time(as_ist_timestamp(tick_time), EXIT_CANDLE_MINUTES)

    with state_lock:
        has_position = any(p["symbol"] == symbol for p in open_positions.values())
        new_bucket = last_exit_bucket.get(symbol) != bucket
        last_exit_bucket[symbol] = bucket

        if not has_position:
            exit_retry_at.pop(symbol, None)
            return

        retry_due = (
            symbol in exit_retry_at and time.monotonic() >= exit_retry_at[symbol]
        )
        if not (new_bucket or retry_due):
            return

        if symbol in exit_inflight:
            # Do not lose this bucket's check; retry shortly.
            exit_retry_at[symbol] = time.monotonic() + 2
            return

        exit_inflight.add(symbol)

    EXIT_EXECUTOR.submit(_exit_worker, symbol,bucket)


# ============================================================
# DHAN WEBSOCKET CALLBACKS
# ============================================================

def on_message(*args) -> None:
    """SDK callback supplies (feed_instance, parsed_message)."""
    message = args[-1] if args else None

    if isinstance(message, (bytes, bytearray)):
        print("[WS] Received raw binary packet; SDK callback did not parse it.")
        return

    if isinstance(message, str):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            return

    if not isinstance(message, dict):
        return

    packet_type = str(message.get("type", "")).lower()
    if "quote" not in packet_type and "full" not in packet_type:
        return

    security_id = str(message.get("security_id", ""))
    symbol = SECURITY_TO_SYMBOL.get(security_id)
    if symbol is None:
        return

    try:
        now = get_ist_now()
        tick_time = (
            resolve_tick_time(message.get("LTT"), now)
            if USE_EXCHANGE_LTT else now
        )

        # Ignore pre-open / post-close ticks entirely.
        if not in_session(tick_time):
            return

        ltp = float(message.get("LTP", 0))
        cumulative_volume = message.get("volume")
        cumulative_volume = (
            int(cumulative_volume) if cumulative_volume is not None else None
        )

        update_live_candle(
            symbol=symbol,
            ltp=ltp,
            cumulative_day_volume=cumulative_volume,
            tick_time=tick_time,
        )

        check_sl_tp(symbol, ltp)
        maybe_check_exit(symbol, tick_time)
        schedule_signal_eval(symbol)

    except Exception as exc:
        print(f"[WS MESSAGE ERROR] {symbol}: {exc}")


def on_connect(*args) -> None:
    print(f"[WS CONNECTED] {get_ist_now():%Y-%m-%d %H:%M:%S %Z}")


def on_close(*args) -> None:
    print(f"[WS CLOSED] {args}")


def on_error(*args) -> None:
    print(f"[WS ERROR] {args}")


# ============================================================
# START WEBSOCKET
# ============================================================

def build_subscriptions():
    instruments = []
    for symbol, info in DHAN_SYMBOLS.items():
        segment = info.get("exchange_segment", "NSE_EQ")
        if segment != "NSE_EQ" and segment != "MCX_COMM":
            raise ValueError(
                f"{symbol}: this script maps equity symbols; "
                f"got unsupported segment {segment!r}"
            )
        if segment == "NSE_EQ":
            instruments.append(
                (MarketFeed.NSE, str(info["security_id"]), FEED_MODE)
            )
        elif segment == "MCX_COMM":
            instruments.append(
                (MarketFeed.MCX, str(info["security_id"]), FEED_MODE)
            )
    return instruments


def run_websocket_forever() -> None:
    instruments = build_subscriptions()
    if not instruments:
        raise RuntimeError("DHAN_SYMBOLS is empty.")

    context = DhanContext(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

    while True:
        feed = None
        try:
            print(
                f"[WS STARTING] Subscribing {len(instruments)} instruments "
                f"at {get_ist_now():%H:%M:%S}"
            )
            feed = MarketFeed(
                context,
                instruments,
                version="v2",
                on_connect=on_connect,
                on_message=on_message,
                on_close=on_close,
                on_error=on_error,
            )
            feed.run()

        except KeyboardInterrupt:
            print("[STOP] Keyboard interrupt received.")
            if feed is not None:
                try:
                    feed.close_connection()
                except Exception:
                    pass
            break

        except Exception as exc:
            print(f"[WS RECONNECT] {exc}")

        finally:
            if feed is not None:
                try:
                    feed.close_connection()
                except Exception:
                    pass

        print("[WS] Reconnecting in 5 seconds...")
        time.sleep(5)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    global DHAN_SYMBOLS, SECURITY_TO_SYMBOL

    print("=" * 65)
    print("DHAN WEBSOCKET LIVE 15-MINUTE STRATEGY (patched)")
    print(f"Started: {get_ist_now():%Y-%m-%d %H:%M:%S %Z}")
    print(f"Symbols: {len(DHAN_SYMBOLS)}")
    print(f"Paper mode: {PAPER_MODE}")
    print(f"Sandbox orders enabled: {ENABLE_SANDBOX_ORDERS}")
    print(
        f"Session {SESSION_START}-{SESSION_END} | entry cutoff {ENTRY_CUTOFF} | "
        f"square-off {SQUARE_OFF_TIME} | ATR SL/TP: {USE_ATR_SL_TP}"
    )
    print("=" * 65)

    warm_up_all_symbols()

    ready_symbols = set(market_frames)
    if not ready_symbols:
        raise RuntimeError("No symbols were warmed up; WebSocket not started.")

    failed = [s for s in DHAN_SYMBOLS if s not in ready_symbols]
    if failed:
        print(f"[WARN] {len(failed)} symbols failed warm-up and are skipped: {failed}")

    DHAN_SYMBOLS = {
        symbol: info
        for symbol, info in DHAN_SYMBOLS.items()
        if symbol in ready_symbols
    }
    SECURITY_TO_SYMBOL = {
        str(info["security_id"]): symbol
        for symbol, info in DHAN_SYMBOLS.items()
    }

    threading.Thread(target=session_watchdog, daemon=True).start()

    run_websocket_forever()


if __name__ == "__main__":
    main()