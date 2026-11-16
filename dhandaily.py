import os
import time
import uuid

import httpx
import requests
import datetime
import pandas as pd

import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator
import time
import datetime
import requests

import dhan_symbols

# ======================================
# TELEGRAM CONFIG
# ======================================
TELEGRAM_BOT_TOKEN = dhan_symbols.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID   = dhan_symbols.TELEGRAM_CHAT_ID

def send_telegram_message(message: str) -> None:
    """
    WEBHOOK_URL = "https://discord.com/api/webhooks/1516478144696291380/Z8Mw-v7_s2p9VmpEmnbCOVBvKm75OUHR3LV-bXOhKsCvHUH62W7ws8FEMCDpQEDPHmLv"
    response = requests.post(
    WEBHOOK_URL,
    json={"content": message}
    )

    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        if not response.ok:
            print(f"Telegram warning: {response.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")


# ======================================
# PARAMETERS
# ======================================
INTERVAL          = "15m"
PERIOD            = "60d"

EMA_FAST          = 20
EMA_SLOW          = 50
EMA_REGIME        = 200        # NEW: regime filter period

VOLUME_MULTIPLIER = 1
ROLLING_SWING     = 20
ATR_PERIOD        = 14

TP_ATR_MULT       = 2.5        # CHANGED: was 2.0 — gives winners more room
SL_ATR_MULT       = 1.0

RSI_LONG_MIN      = 40         # CHANGED: was 45 — slightly wider band
RSI_LONG_MAX      = 70         # CHANGED: was 65
RSI_SHORT_MIN     = 30         # CHANGED: was 35
RSI_SHORT_MAX     = 60         # CHANGED: was 55

BODY_RATIO_MIN    = 0.30       # NEW: min candle body / range ratio for confirmation
SIGNAL_COOLDOWN   = 3          # NEW: min bars between signals per symbol


# Tracks sent signals { symbol: [timestamp_str, ...] } — prevents duplicate Telegram alerts
signal_dict: dict[str, list[str]] = {}

# Tracks last signal bar index per symbol — used for cooldown
last_signal_bar: dict[str, int] = {}


# ======================================
# HELPERS
# ======================================
def get_ist_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).astimezone(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    )

def create_beep_sound() -> None:
    print("🔔 Signal alert")

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns that yfinance sometimes returns."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    else:
        df.columns = [str(col) for col in df.columns]
    return df

def _localize_to_ist(df: pd.DataFrame) -> pd.DataFrame:
    tz = "Asia/Kolkata"
    if df["Datetime"].dt.tz is None:
        df["Datetime"] = df["Datetime"].dt.tz_localize("UTC").dt.tz_convert(tz)
    else:
        df["Datetime"] = df["Datetime"].dt.tz_convert(tz)
    return df

DHAN_CLIENT_ID = dhan_symbols.DHAN_CLIENT_ID
DHAN_ACCESS_TOKEN = dhan_symbols.DHAN_ACCESS_TOKEN_DAILYSCRIPT

DHAN_INTRADAY_URL = "https://api.dhan.co/v2/charts/intraday"




DHAN_SYMBOLS = {
    # "RELIANCE.NS": {
    #     "security_id": "2885",
    #     "exchange_segment": "NSE_EQ",
    #     "instrument": "EQUITY",
    # },
    # "POLYCAB.NS": {
    #     "security_id": "9590",
    #     "exchange_segment": "NSE_EQ",
    #     "instrument": "EQUITY",
    # },
    # "ABBOTINDIA.NS": {
        #         "security_id": "17903",
        #         "exchange_segment": "NSE_EQ",
        #         "instrument": "EQUITY",
        #     },
    #  "NAVINFLUOR.NS": {
    #         "security_id": "14672",
    #         "exchange_segment": "NSE_EQ",
    #         "instrument": "EQUITY",
    #     },
    # "ICICIGI.NS": {
    #         "security_id": "21770",
    #         "exchange_segment": "NSE_EQ",
    #         "instrument": "EQUITY",
    #     },
    "OFSS.NS": {
            "security_id": "10738",
            "exchange_segment": "NSE_EQ",
            "instrument": "EQUITY",
        },
}

# DHAN_SYMBOLS=dhan_symbols.DHAN_SYMBOLS

def get_ist_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).astimezone(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    )


def download_dhan_chunk(
    symbol,
    security_id,
    exchange_segment,
    instrument,
    start_date,
    end_date,
):
    """
    Download one chunk of intraday data from Dhan.

    Dhan expects interval values such as '15', not '15m'.
    """
    if not DHAN_ACCESS_TOKEN:
        raise RuntimeError("Set the DHAN_ACCESS_TOKEN environment variable.")

    if not DHAN_CLIENT_ID:
        raise RuntimeError("Set the DHAN_CLIENT_ID environment variable.")
    print(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}")
    payload = {
        "securityId": str(security_id),
        "exchangeSegment": exchange_segment,
        "instrument": instrument,
        "interval": "15",
        "oi": False,
        "fromDate": start_date.strftime("%Y-%m-%d"),
        "toDate": end_date.strftime("%Y-%m-%d"),
    }

    headers = {
        "access-token": DHAN_ACCESS_TOKEN,
        "client-id": DHAN_CLIENT_ID,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = requests.post(
        DHAN_INTRADAY_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if int(response.status_code) == 429:
        time.sleep(1)  # Wait a bit before retrying
        response = requests.post(
                DHAN_INTRADAY_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )

    data = response.json()

    required = ("open", "high", "low", "close", "volume", "timestamp")

    if not all(key in data for key in required):
        raise RuntimeError(
            f"Unexpected Dhan response for {symbol}: "
            f"{str(data)[:500]}"
        )

    lengths = {len(data[key]) for key in required}

    if len(lengths) != 1:
        raise RuntimeError(
            f"Mismatched OHLCV array lengths for {symbol}"
        )

    if not data["timestamp"]:
        return pd.DataFrame(
            columns=[
                "Datetime", "Open", "High",
                "Low", "Close", "Volume"
            ]
        )

    # Dhan timestamps are Unix epoch timestamps in seconds.
    # Convert to UTC first, then to Indian Standard Time.
    df = pd.DataFrame({
        "Datetime": pd.to_datetime(
            data["timestamp"],
            unit="s",
            utc=True,
        ).tz_convert("Asia/Kolkata"),
        "Open": data["open"],
        "High": data["high"],
        "Low": data["low"],
        "Close": data["close"],
        "Volume": data["volume"],
    })

    return df


def download_dhan_data(
    symbol,
    period_days=60,
    interval="15m",
):
    """
    Download intraday candles over multiple requests.

    Each request covers no more than 90 days.
    """
    if symbol not in DHAN_SYMBOLS:
        raise ValueError(
            f"{symbol} is not mapped in DHAN_SYMBOLS. "
            "Add its verified Dhan security ID."
        )

    if interval not in {"1m", "5m", "15m", "25m", "60m"}:
        raise ValueError("Unsupported Dhan intraday interval.")

    symbol_info = DHAN_SYMBOLS[symbol]

    end_date = get_ist_now().replace(tzinfo=None)
    start_date = end_date - datetime.timedelta(days=period_days)

    chunks = []
    chunk_start = start_date

    payload_df = download_dhan_chunk(
        symbol=symbol,
        security_id=symbol_info["security_id"],
        exchange_segment=symbol_info["exchange_segment"],
        instrument=symbol_info["instrument"],
        start_date=chunk_start,
        end_date=end_date,
    )

    if not payload_df.empty:
        chunks.append(payload_df)

    chunk_start = end_date
    time.sleep(0.25)

    if not chunks:
        return pd.DataFrame(
            columns=[
                "Datetime", "Open", "High",
                "Low", "Close", "Volume"
            ]
        )

    result = pd.concat(chunks, ignore_index=True)

    result = (
        result.drop_duplicates(subset="Datetime")
        .sort_values("Datetime")
        .reset_index(drop=True)
    )

    return result,symbol

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


MAX_DOWNLOAD_WORKERS=5

MAX_DOWNLOAD_WORKERS = 5
BATCH_WAIT_SECONDS = 0.43


def download_data():
    now = get_ist_now()
    overall_started = time.perf_counter()

    symbols = list(DHAN_SYMBOLS.keys())
    total_symbols = len(symbols)

    total_batches = (
        total_symbols + MAX_DOWNLOAD_WORKERS - 1
    ) // MAX_DOWNLOAD_WORKERS

    downloaded_count = 0
    processed_count = 0

    # print(
    #     f"Starting scan for {total_symbols} stocks "
    #     f"at {now:%H:%M:%S}"
    # )

    # Process five stocks at a time.
    for batch_start in range(
        0,
        total_symbols,
        MAX_DOWNLOAD_WORKERS,
    ):
        batch = symbols[
            batch_start:
            batch_start + MAX_DOWNLOAD_WORKERS
        ]

        batch_number = (
            batch_start // MAX_DOWNLOAD_WORKERS
        ) + 1

        print(
            # f"\n========== BATCH "
            f"{batch_number}/{total_batches} =========="
        )

        batch_started = time.perf_counter()
        batch_data = {}

        # --------------------------------------------
        # STEP 1: DOWNLOAD FIVE STOCKS CONCURRENTLY
        # --------------------------------------------

        with ThreadPoolExecutor(
            max_workers=MAX_DOWNLOAD_WORKERS
        ) as executor:

            futures = {
                executor.submit(
                    download_dhan_data,
                    symbol=symbol,
                    period_days=60,
                    interval=INTERVAL,
                ): symbol
                for symbol in batch
            }

            for future in as_completed(futures):
                symbol = futures[future]

                try:
                    df, result_symbol = future.result()

                    if df is None or df.empty:
                        print(
                            f"[DOWNLOAD ERROR] "
                            f"{symbol}: No data returned"
                        )
                        continue

                    df = df.dropna(
                        subset=[
                            "Open",
                            "High",
                            "Low",
                            "Close",
                            "Volume",
                        ]
                    ).copy()

                    if df.empty:
                        print(
                            f"[DOWNLOAD ERROR] "
                            f"{symbol}: No valid candles"
                        )
                        continue

                    batch_data[result_symbol] = df
                    downloaded_count += 1

                    # print(
                    #     f"[DOWNLOAD SUCCESS] "
                    #     f"{result_symbol}: "
                    #     f"{len(df)} candles"
                    # )

                except Exception as exc:
                    print(
                        f"[WORKER ERROR] {symbol}: {exc}"
                    )

        # --------------------------------------------
        # STEP 2: PROCESS SIGNALS FOR THIS BATCH
        # --------------------------------------------

        print(
            f"\n[PROCESSING] Batch {batch_number}"
        )

        for symbol in batch:
            df = batch_data.get(symbol)

            if df is None or df.empty:
                continue

            try:
                signals = compute_indicators_and_signals(
                    df,
                    symbol,
                    now,
                )

                processed_count += 1

                if signals:
                    print(
                        f"[SIGNALS] {symbol}: {signals}"
                    )
                else:
                    print(
                        f"[NO SIGNAL] {symbol}"
                    )

            except Exception as exc:
                print(
                    f"[STRATEGY ERROR] {symbol}: {exc}"
                )

        # batch_elapsed = (
        #     time.perf_counter() - batch_started
        # )

        # print(
        #     f"\n[BATCH COMPLETE] "
        #     f"{batch_number}/{total_batches} | "
        #     f"Downloaded: {len(batch_data)}/{len(batch)} | "
        #     f"Duration: {batch_elapsed:.2f}s"
        # )

        # --------------------------------------------
        # STEP 3: WAIT BEFORE THE NEXT BATCH
        # --------------------------------------------

        has_remaining_stocks = (
            batch_start + MAX_DOWNLOAD_WORKERS
            < total_symbols
        )

        if has_remaining_stocks:
            # print(
            #     f"[WAIT] Waiting "
            #     f"{BATCH_WAIT_SECONDS:.1f} seconds "
            #     f"before the next batch"
            # )

            time.sleep(BATCH_WAIT_SECONDS)

    # --------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------

    total_elapsed = (
        time.perf_counter() - overall_started
    )

    print("\n========== SCAN SUMMARY ==========")
    print(f"Total stocks: {total_symbols}",now)
    print(f"Downloaded: {downloaded_count}")
    print(f"Processed: {processed_count}")
    print(f"Total time: {total_elapsed:.2f}s")

# ======================================
# POSITION MANAGEMENT  (paste this block ABOVE compute_indicators_and_signals)
# ======================================
open_positions: dict[str, dict] = {}   # { symbol: {side, entry_price, entry_time, qty} }
closed_trades: list[dict] = []         # history of closed trades
total_pnl_rs: float = 0.0              # cumulative realised profit in ₹
total_invested_rs: float = 0.0         # cumulative capital deployed in closed trades


# Telegram messages execute in background threads.
TELEGRAM_EXECUTOR = ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="telegram"
)

def send_telegram_message_background(message: str) -> None:
    """
    Schedule Telegram delivery without blocking the caller.
    """
    try:
        TELEGRAM_EXECUTOR.submit(
            send_telegram_message,
            message,
        )
    except RuntimeError as exc:
        print(f"Could not schedule Telegram message: {exc}")


def get_quantity(price: float) -> int:
    """Quantity slabs based on stock price."""
    if price < 1000:
        return 400
    elif price < 3000:
        return 100
    else:
        return 50

DHAN_Place_Order_URL = "https://sandbox.dhan.co/v2/orders"
DHAN_Sandbox_ACCESS_TOKEN="eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA4MDg5MTQ5Iiwid2ViaG9va1VybCI6IiIsImlzcyI6ImRoYW4iLCJleHAiOjE3OTM3NjM5NTF9.7gIHG2Xjq2gBbaDa5IaXt_TDUNQQnZIXmD2nSzTLJlWVsjUGEfWcbZequayllhlL_QxPEIYv9ORwaavvTi8Ysw"
DHAN_Sandbox_ClientId="1108089149"

def place_sandbox_order(transactionType, symbol, quantity):
    # print("\n========== DHAN SANDBOX ORDER ==========")
    # print(f"Order placement started: {symbol}")

    if not DHAN_Sandbox_ClientId or not DHAN_Sandbox_ACCESS_TOKEN:
        print("Configure DHAN_Sandbox_ClientId and DHAN_Sandbox_ACCESS_TOKEN.")

    # Validate transaction type.
    transactionType = str(transactionType).upper()

    if transactionType not in ("BUY", "SELL"):
        print("transactionType must be BUY or SELL.")

    # Validate quantity.
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        print("Quantity must be a positive integer.")
        

    if quantity <= 0:
        print("Quantity must be greater than zero.")
        

    # Validate symbol.
    symbol_info = DHAN_SYMBOLS.get(symbol)

    if not symbol_info:
        print(f"Symbol {symbol} not found in DHAN_SYMBOLS.")
        return

    # Build the order payload.
    payload = {
        "dhanClientId": DHAN_Sandbox_ClientId,
        # "correlationId": uuid.uuid4().hex[:30],
        "transactionType": transactionType,
        "exchangeSegment": symbol_info.get(
            "exchange_segment", "NSE_EQ"
        ),
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": str(symbol_info["security_id"]),
        "quantity": quantity,
        # "disclosedQuantity": 0,
        # "price": 0,
        # "triggerPrice": 0,
        # "afterMarketOrder": 'false',
        # "amoTime": "",
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "access-token": DHAN_Sandbox_ACCESS_TOKEN,
    }
    try:
        response = requests.post(
            DHAN_Place_Order_URL,
            json=payload,
            headers=headers,
            timeout=5,
        )

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"response_text": response.text}

        print("Parsed Response:", response_data)

        if not response.ok:
            print(f"Order rejected for {symbol}")
            print("Response:", response_data)
            


        return {
            "mode": "DHAN_SANDBOX",
            "symbol": symbol,
            "request": payload,
            "response": response_data,
        }


    except requests.exceptions.Timeout:
        print(f"Request timed out for {symbol}.")
        

    except requests.exceptions.RequestException as exc:
        print(f"Connection error for {symbol}: {exc}")
        

    except Exception as exc:
        print(f"Unexpected error for {symbol}: {exc}")
        
        
# Telegram messages execute in background threads.
ORDER_EXECUTOR = ThreadPoolExecutor(
    max_workers=5,
    thread_name_prefix="order_position"
)

def start_order_execution_background(transactionType,symbol,quantity) -> None:
    """
    Schedule order delivery without blocking the caller.
    """
    try:
        ORDER_EXECUTOR.submit(
            place_sandbox_order,
            transactionType=transactionType,
            symbol=symbol,
            quantity=quantity
        )
    except RuntimeError as exc:
        print(f"Could not schedule order: {exc}")

def enter_position(symbol: str, side: str, entry_price: float, entry_time) -> None:
    """Open a position when a BUY/SELL signal is generated."""
    # if symbol in open_positions:           # one open position per symbol
    #     return

    qty = get_quantity(entry_price)
    open_positions[f'{symbol}_{entry_time}'] = {
        "symbol": symbol,
        "side": side,
        "entry_price": entry_price,
        "entry_time": entry_time,
        "qty": qty,
    }
    # 🟢
    msg = (
        f"ENTRY [{side}]\n"
        f"Symbol      : {symbol}\n"
        f"Entry Time  : {entry_time}\n"
        f"Entry Price : {entry_price:.2f}\n"
        f"Qty         : {qty}\n"
        f"Value       : {entry_price * qty:,.2f}"
        f"Daily Strategy : True"
    )
    print(msg)
    with open("trade_log_new.txt1", "a") as f:
            f.write(msg + "\n\n")
    send_telegram_message_background(msg)
    # start_order_execution_background(transactionType=side,symbol=symbol,quantity=qty)
    


def exit_position(symbol: str, exit_price: float, exit_time) -> None:
    """Close the open position and print / send entry, exit, P&L in ₹ and %."""
    global total_pnl_rs, total_invested_rs

    pos = open_positions.pop(symbol, None)
    if pos is None:
        return

    side, entry, qty = pos["side"], pos["entry_price"], pos["qty"]
    pnl_rs = (exit_price - entry) * qty if side == "BUY" else (entry - exit_price) * qty
    invested = entry * qty
    pnl_pct = (pnl_rs / invested) * 100

    total_pnl_rs += pnl_rs
    total_invested_rs += invested
    total_pct = (total_pnl_rs / total_invested_rs) * 100 if total_invested_rs else 0.0

    closed_trades.append({
        "symbol": pos["symbol"], "side": side, "qty": qty,
        "entry_time": pos["entry_time"], "entry_price": entry,
        "exit_time": exit_time, "exit_price": exit_price,
        "pnl_rs": pnl_rs, "pnl_pct": pnl_pct,
    })

    icon = "✅" if pnl_rs >= 0 else "🔴"
    msg = (
        f"EXIT [{side}]\n"
        f"Symbol      : {pos['symbol']}\n"
        f"Entry       : {entry:.2f}  @ {pos['entry_time']}\n"
        f"Exit        : {exit_price:.2f}  @ {exit_time}\n"
        f"Qty         : {qty}\n"
        f"Trade P&L   : {pnl_rs:,.2f}  ({pnl_pct:+.2f}%)\n"
        f"Total P&L   : {total_pnl_rs:,.2f}  ({total_pct:+.2f}%)\n"
        f"Closed trades: {len(closed_trades)}\n"
        f"Daily Strategy : True"
    )
    print(msg)
    with open("trade_log_new.txt1", "a") as f:
        f.write(msg + "\n\n")
    send_telegram_message_background(msg)
    symbol = pos["symbol"]
    trans_type = "SELL" if side.upper() == "BUY" else "BUY"
    # start_order_execution_background(transactionType=trans_type,symbol=symbol,quantity=qty)
    



def get_5min_candles(
    dhan_client_id: str,
    dhan_access_token: str,
    security_id: str,
    exchange_segment: str = "NSE_EQ",
    instrument_type: str = "EQUITY",
    start_date=None,
    end_date=None,
) -> pd.DataFrame:

    url = "https://api.dhan.co/v2/charts/intraday"

    headers = {
        "access-token": dhan_access_token,
        "client-id": dhan_client_id,
        "Content-Type": "application/json",
    }
    
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').date()
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').date()
    payload = {
            "securityId": str(security_id),
            "exchangeSegment": exchange_segment,
            "instrument": instrument_type,
            "interval": "5",
            "oi": False,
            "fromDate": start_date.strftime('%Y-%m-%d'),   # "2026-11-01"
            "toDate": end_date.strftime('%Y-%m-%d'),
        }
    
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=15,
    )
    if response.status_code != 200:
        time.sleep(1)  # Wait a bit before retrying
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )
    response.raise_for_status()

    data = response.json()

    if not data.get("timestamp"):
        return pd.DataFrame(
            columns=["Datetime", "Open", "High", "Low", "Close", "Volume"]
        )

    df = pd.DataFrame({
    "Datetime": pd.to_datetime(data["timestamp"], unit="s", utc=True)
                  .tz_convert("Asia/Kolkata"),
    "Open": data["open"],
    "High": data["high"],
    "Low": data["low"],
    "Close": data["close"],
    "Volume": data["volume"],
    })

    return df.sort_values("Datetime").reset_index(drop=True)



def check_exit(symbol: str,df=None) -> None:
    
    # print(f"Checking exit conditions for open positions: {open_positions}")
    for key in list(open_positions.keys()):
        pos = open_positions.get(key)
        if pos is None:
            continue
        
        symbol = pos["symbol"]
        symbol_info = DHAN_SYMBOLS[symbol]
        df = get_5min_candles(
        dhan_client_id=DHAN_CLIENT_ID,
        dhan_access_token=DHAN_ACCESS_TOKEN,
        security_id=symbol_info["security_id"],
        start_date=pos["entry_time"].strftime("%Y-%m-%d %H:%M:%S"),
        end_date=pos["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
        )
        
        entry_ts = pd.Timestamp(pos["entry_time"])
        
        position_type = pos["side"].upper()

        df = df.sort_values("Datetime").reset_index(drop=True)

        for i in range(1, len(df)):

            candle_time = df.loc[i, "Datetime"]

            if candle_time <= entry_ts:
                continue

            curr_close = float(df.loc[i, "Close"])
            prev_close = float(df.loc[i - 1, "Open"])

            should_exit = (
                position_type == "BUY" and curr_close < prev_close
            ) or (
                position_type == "SELL" and curr_close > prev_close
            )

            if should_exit:
                exit_position(key, curr_close, candle_time)
                break  # Exit after closing the position; no need to check further candles for this position
        # print(open_positions)
                
    return


# ======================================
# HOOKS — the only edits inside compute_indicators_and_signals
# ======================================
# 1) In the BUY block, right after send_telegram_message(...) add:
#        enter_position(symbol, "BUY", float(row["Open"]), ts)
#
# 2) In the SELL block, right after send_telegram_message(...) add:
#        enter_position(symbol, "SELL", float(row["Open"]), ts)
#
# 3) After the `for _, row in df.iterrows():` loop, just before `return signals`, add:
#        check_exit(symbol, df)


# ======================================
# INDICATORS + IMPROVED SIGNALS
# ======================================
def compute_indicators_and_signals(
    df: pd.DataFrame,
    symbol: str,
    now: datetime.datetime,
) -> list[list]:

    # ── Trend indicators ──────────────────────────────────────────────────────
    df["EMA20"]  = EMAIndicator(df["Close"], window=EMA_FAST).ema_indicator()
    df["EMA50"]  = EMAIndicator(df["Close"], window=EMA_SLOW).ema_indicator()
    df["EMA200"] = EMAIndicator(df["Close"], window=EMA_REGIME).ema_indicator()  # NEW

    # ── Volume ────────────────────────────────────────────────────────────────
    df["vol_ma20"] = df["Volume"].rolling(20, min_periods=1).mean()

    # ── Volatility ────────────────────────────────────────────────────────────
    atr = AverageTrueRange(df["High"], df["Low"], df["Close"], window=ATR_PERIOD)
    df["ATR14"]      = atr.average_true_range()
    df["ATR14_MA20"] = df["ATR14"].rolling(20).mean()

    # ── Swing high/low (liquidity levels) ────────────────────────────────────
    df["prev_high"] = df["High"].shift(1).rolling(ROLLING_SWING).max()
    df["prev_low"]  = df["Low"].shift(1).rolling(ROLLING_SWING).min()

    # ── Sweep detection ───────────────────────────────────────────────────────
    df["sweep_long"]  = (df["Low"] < df["prev_low"])  & (df["Close"] > df["prev_low"])
    df["sweep_short"] = (df["High"] > df["prev_high"]) & (df["Close"] < df["prev_high"])

    # ── Trend direction — now includes EMA200 regime (CHANGED) ───────────────
    df["trend_long"]  = (df["EMA20"] > df["EMA50"]) & (df["Close"] > df["EMA200"])
    df["trend_short"] = (df["EMA20"] < df["EMA50"]) & (df["Close"] < df["EMA200"])

    # ── Volume confirmation — now wired into signals (FIX) ───────────────────
    df["vol_confirm"] = df["Volume"] > (VOLUME_MULTIPLIER * df["vol_ma20"])

    # ── ATR expansion ─────────────────────────────────────────────────────────
    df["atr_confirm"] = df["ATR14"] > df["ATR14_MA20"]

    # ── RSI — widened bands (CHANGED) ─────────────────────────────────────────
    df["RSI14"]     = RSIIndicator(df["Close"], window=14).rsi()
    df["rsi_long"]  = (df["RSI14"] > RSI_LONG_MIN)  & (df["RSI14"] < RSI_LONG_MAX)
    df["rsi_short"] = (df["RSI14"] < RSI_SHORT_MAX) & (df["RSI14"] > RSI_SHORT_MIN)

    # ── Candle body confirmation (NEW) ────────────────────────────────────────
    candle_range    = (df["High"] - df["Low"]).replace(0, np.nan)
    df["body_long"]  = (df["Close"] - df["Open"]) / candle_range > BODY_RATIO_MIN
    df["body_short"] = (df["Open"] - df["Close"]) / candle_range > BODY_RATIO_MIN

    # ── Composite signals — all filters must fire ─────────────────────────────
    df["BUY_SIGNAL"] = (
        df["sweep_long"]
        & df["trend_long"]
        & df["atr_confirm"]
        & df["rsi_long"]
        & df["vol_confirm"]   # FIX: was missing
        & df["body_long"]     # NEW
    )
    df["SELL_SIGNAL"] = (
        df["sweep_short"]
        & df["trend_short"]
        & df["atr_confirm"]
        & df["rsi_short"]
        & df["vol_confirm"]   # FIX: was missing
        & df["body_short"]    # NEW
    )

    # ── Emit signals ──────────────────────────────────────────────────────────
    signals: list[list] = []
    seen_times = signal_dict.get(symbol, [])
    last_bar   = last_signal_bar.get(symbol, -SIGNAL_COOLDOWN)
    bar_idx    = 0   # approximate bar counter for cooldown

    for _, row in df.iterrows():
        ts = row["Datetime"]

        # Cooldown: skip if fewer than SIGNAL_COOLDOWN bars since last alert
        if bar_idx - last_bar < SIGNAL_COOLDOWN:
            bar_idx += 1
            continue

        if row["BUY_SIGNAL"]:
            signals.append([str(ts), "BUY", round(float(row["Close"]), 2)])
            if str(ts) not in seen_times and ts.date() == now.date()-datetime.timedelta(days=2):
                seen_times.append(str(ts))
                signal_dict[symbol] = seen_times
                last_signal_bar[symbol] = bar_idx
                create_beep_sound()
                # send_telegram_message(
                #     f"📈 BUY SIGNAL [v2]\n"
                #     f"Symbol : {symbol}\n"
                #     f"Time   : {ts}\n"
                #     f"Price  : {row['Open']:.2f}\n"
                #     f"RSI    : {row['RSI14']:.1f}\n"
                #     f"ATR    : {row['ATR14']:.2f}\n"
                #     f"TP     : {row['Open'] + TP_ATR_MULT * row['ATR14']:.2f}  (+{TP_ATR_MULT}×ATR)\n"
                #     f"SL     : {row['Open'] - SL_ATR_MULT * row['ATR14']:.2f}  (-{SL_ATR_MULT}×ATR)"
                # )
            enter_position(symbol, "BUY", float(row["Close"]), ts)

        elif row["SELL_SIGNAL"]:
            signals.append([str(ts), "SELL", round(float(row["Close"]), 2)])
            if str(ts) not in seen_times and ts.date() == now.date()-datetime.timedelta(days=2):
                seen_times.append(str(ts))
                signal_dict[symbol] = seen_times
                last_signal_bar[symbol] = bar_idx
                create_beep_sound()
                # send_telegram_message(
                #     f"📉 SELL SIGNAL [v2]\n"
                #     f"Symbol : {symbol}\n"
                #     f"Time   : {ts}\n"
                #     f"Price  : {row['Open']:.2f}\n"
                #     f"RSI    : {row['RSI14']:.1f}\n"
                #     f"ATR    : {row['ATR14']:.2f}\n"
                #     f"TP     : {row['Open'] - TP_ATR_MULT * row['ATR14']:.2f}  (-{TP_ATR_MULT}×ATR)\n"
                #     f"SL     : {row['Open'] + SL_ATR_MULT * row['ATR14']:.2f}  (+{SL_ATR_MULT}×ATR)"
                # )
            enter_position(symbol, "SELL", float(row["Close"]), ts)

        bar_idx += 1
    check_exit(symbol,df)
    return signals



if __name__ == "__main__":
    download_data()
    # while True: 
    #     now = datetime.datetime.now()
    #     # if now.minute % 5 == 0 and now.second >= 3:
    #     # if now.time() < datetime.time(9, 15):
    #     #     print(f"⏳ Market not open yet ({now.strftime('%H:%M:%S')}). Waiting...")
    #     #     time.sleep(10)
    #     #     continue
        
    #     print(f"🔄  Scan @ {get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    #     download_data()
        
    #     print(f"✅  Next scan in 5 minutes...\n")
    #     # time.sleep(60)
    #     # time.sleep(1)
    
