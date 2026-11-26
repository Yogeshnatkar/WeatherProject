"""Dhan NSE equity symbol map generated from api-scrip-master-detailed.csv.
Only tickers from the user-provided symbol_list are included.
Verify/update the scrip master regularly because security IDs and listings can change.
"""

DHAN_CLIENT_ID = '1108089149'
DHAN_ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJ1c2VyUmVnaW9uIjoiUjEiLCJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzk1NzQ4Mjc4LCJpYXQiOjE3OTU2NjE4NzgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA4MDg5MTQ5In0.6pLb2nptvU3A9WpJljJL0mXLNYBJfN_6326ecumPjokypyRjecOM4U5bOjxCIUKifv_f_T4IMibIkvFvb7_fKQ'

DHAN_ACCESS_TOKEN_DAILYSCRIPT = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJ1c2VyUmVnaW9uIjoiUjEiLCJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzk1NzQ4MjcwLCJpYXQiOjE3OTU2NjE4NzAsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA4MDg5MTQ5In0.5BJ0L3j3Ph0tbw_TfOa2OdNNvMwv0od8o7Pi0v_zCkYCzOiiYlpXtP0zFN81824ZtUF6fhL2u8bwBY6Otay8Aw'

DHAN_Sandbox_ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA4MDg5MTQ5Iiwid2ViaG9va1VybCI6IiIsImlzcyI6ImRoYW4iLCJleHAiOjE3OTQyODE1NTh9.6ZmscyZ1l8zJuKC07CLscQ9XeM5PJIkVCOtCPOvu4_I-IviwmajZIJTzWJHrnwYoabRv3z9JnieAtEEEt8YW6Q"
DHAN_Sandbox_ClientId = "1108089149"

TELEGRAM_BOT_TOKEN = "8582304947:AAElWIgZcpSlvNdL5ubdoFRI8n_kgqJtSKg"
TELEGRAM_CHAT_ID   = "1315665202"

DHAN_SYMBOLS = {
    "SBIN.NS": {
        "security_id": "3045",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "VEDL.NS": {
        "security_id": "3063",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NHPC.NS": {
        "security_id": "17400",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "INFY.NS": {
        "security_id": "1594",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BANKBARODA.NS": {
        "security_id": "4668",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "COALINDIA.NS": {
        "security_id": "20374",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "AXISBANK.NS": {
        "security_id": "5900",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "APOLLOHOSP.NS": {
        "security_id": "157",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "JUBLFOOD.NS": {
        "security_id": "18096",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SAIL.NS": {
        "security_id": "2963",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ADANIPOWER.NS": {
        "security_id": "17388",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "AMBUJACEM.NS": {
        "security_id": "1270",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BHARTIARTL.NS": {
        "security_id": "10604",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LT.NS": {
        "security_id": "11483",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "RELIANCE.NS": {
        "security_id": "2885",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GODREJCP.NS": {
        "security_id": "10099",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TCS.NS": {
        "security_id": "11536",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "JSWSTEEL.NS": {
        "security_id": "11723",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MARUTI.NS": {
        "security_id": "10999",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NTPC.NS": {
        "security_id": "11630",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ITC.NS": {
        "security_id": "1660",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PERSISTENT.NS": {
        "security_id": "18365",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HDFCBANK.NS": {
        "security_id": "1333",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BAJFINANCE.NS": {
        "security_id": "317",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "INDUSINDBK.NS": {
        "security_id": "5258",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ICICIBANK.NS": {
        "security_id": "4963",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LICI.NS": {
        "security_id": "9480",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LTTS.NS": {
        "security_id": "18564",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BAJAJFINSV.NS": {
        "security_id": "16675",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BIOCON.NS": {
        "security_id": "11373",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BPCL.NS": {
        "security_id": "526",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BRITANNIA.NS": {
        "security_id": "547",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CHOLAFIN.NS": {
        "security_id": "685",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DLF.NS": {
        "security_id": "14732",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HINDALCO.NS": {
        "security_id": "1363",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MARICO.NS": {
        "security_id": "4067",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NESTLEIND.NS": {
        "security_id": "17963",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PAGEIND.NS": {
        "security_id": "14413",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PNB.NS": {
        "security_id": "10666",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SBILIFE.NS": {
        "security_id": "21808",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SHREECEM.NS": {
        "security_id": "3103",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SIEMENS.NS": {
        "security_id": "3150",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TECHM.NS": {
        "security_id": "13538",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ABB.NS": {
        "security_id": "13",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ABBOTINDIA.NS": {
        "security_id": "17903",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ABCAPITAL.NS": {
        "security_id": "21614",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ADANIENT.NS": {
        "security_id": "25",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ADANIGREEN.NS": {
        "security_id": "3563",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ADANIPORTS.NS": {
        "security_id": "15083",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ALKEM.NS": {
        "security_id": "11703",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "APLAPOLLO.NS": {
        "security_id": "25780",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ASHOKLEY.NS": {
        "security_id": "212",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ASTRAL.NS": {
        "security_id": "14418",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "AUROPHARMA.NS": {
        "security_id": "275",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BANDHANBNK.NS": {
        "security_id": "2263",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BEL.NS": {
        "security_id": "383",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BHEL.NS": {
        "security_id": "438",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CANBK.NS": {
        "security_id": "10794",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CGPOWER.NS": {
        "security_id": "760",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CIPLA.NS": {
        "security_id": "694",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CUMMINSIND.NS": {
        "security_id": "1901",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DABUR.NS": {
        "security_id": "772",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DEEPAKNTR.NS": {
        "security_id": "19943",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DIVISLAB.NS": {
        "security_id": "10940",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DMART.NS": {
        "security_id": "19913",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ESCORTS.NS": {
        "security_id": "958",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "FEDERALBNK.NS": {
        "security_id": "1023",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GAIL.NS": {
        "security_id": "4717",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GLENMARK.NS": {
        "security_id": "7406",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HAL.NS": {
        "security_id": "2303",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HAVELLS.NS": {
        "security_id": "9819",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HEROMOTOCO.NS": {
        "security_id": "1348",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HINDUNILVR.NS": {
        "security_id": "1394",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HUDCO.NS": {
        "security_id": "20825",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IDFCFIRSTB.NS": {
        "security_id": "11184",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "INDIGO.NS": {
        "security_id": "11195",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "INDUSTOWER.NS": {
        "security_id": "29135",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IRCTC.NS": {
        "security_id": "13611",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IREDA.NS": {
        "security_id": "20261",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IRFC.NS": {
        "security_id": "2029",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "JINDALSTEL.NS": {
        "security_id": "6733",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "KPITTECH.NS": {
        "security_id": "9683",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LUPIN.NS": {
        "security_id": "10440",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MANKIND.NS": {
        "security_id": "15380",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MAZDOCK.NS": {
        "security_id": "509",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MCX.NS": {
        "security_id": "31181",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MOTHERSON.NS": {
        "security_id": "4204",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MPHASIS.NS": {
        "security_id": "4503",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MUTHOOTFIN.NS": {
        "security_id": "23650",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NAUKRI.NS": {
        "security_id": "13751",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NMDC.NS": {
        "security_id": "15332",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "OBEROIRLTY.NS": {
        "security_id": "20242",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "OFSS.NS": {
        "security_id": "10738",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ONGC.NS": {
        "security_id": "2475",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PAYTM.NS": {
        "security_id": "6705",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PETRONET.NS": {
        "security_id": "11351",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PHOENIXLTD.NS": {
        "security_id": "14552",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PIDILITIND.NS": {
        "security_id": "2664",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PIIND.NS": {
        "security_id": "24184",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "POLICYBZR.NS": {
        "security_id": "6656",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "POLYCAB.NS": {
        "security_id": "9590",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "POWERGRID.NS": {
        "security_id": "14977",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PRESTIGE.NS": {
        "security_id": "20302",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "RBLBANK.NS": {
        "security_id": "18391",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SRF.NS": {
        "security_id": "3273",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SUNPHARMA.NS": {
        "security_id": "3351",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SUPREMEIND.NS": {
        "security_id": "3363",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TATACHEM.NS": {
        "security_id": "3405",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TATACOMM.NS": {
        "security_id": "3721",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TATACONSUM.NS": {
        "security_id": "3432",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TATAPOWER.NS": {
        "security_id": "3426",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TATASTEEL.NS": {
        "security_id": "3499",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TIINDIA.NS": {
        "security_id": "312",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TORNTPHARM.NS": {
        "security_id": "3518",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TRENT.NS": {
        "security_id": "1964",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TVSMOTOR.NS": {
        "security_id": "8479",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ULTRACEMCO.NS": {
        "security_id": "11532",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "UNIONBANK.NS": {
        "security_id": "10753",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "UPL.NS": {
        "security_id": "11287",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "VBL.NS": {
        "security_id": "18921",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ZYDUSLIFE.NS": {
        "security_id": "7929",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "WIPRO.NS": {
        "security_id": "3787",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HCLTECH.NS": {
        "security_id": "7229",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "KOTAKBANK.NS": {
        "security_id": "1922",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ASIANPAINT.NS": {
        "security_id": "236",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TITAN.NS": {
        "security_id": "3506",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DRREDDY.NS": {
        "security_id": "881",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "EICHERMOT.NS": {
        "security_id": "910",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BAJAJ-AUTO.NS": {
        "security_id": "16669",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "M&M.NS": {
        "security_id": "2031",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GRASIM.NS": {
        "security_id": "1232",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HDFCLIFE.NS": {
        "security_id": "467",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SHRIRAMFIN.NS": {
        "security_id": "4306",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ETERNAL.NS": {
        "security_id": "5097",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HINDPETRO.NS": {
        "security_id": "1406",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HINDZINC.NS": {
        "security_id": "1424",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IOC.NS": {
        "security_id": "1624",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PFC.NS": {
        "security_id": "14299",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "RVNL.NS": {
        "security_id": "9552",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IRCON.NS": {
        "security_id": "4986",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "RITES.NS": {
        "security_id": "3761",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CONCOR.NS": {
        "security_id": "4749",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "OIL.NS": {
        "security_id": "17438",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SJVN.NS": {
        "security_id": "18883",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NLCINDIA.NS": {
        "security_id": "8585",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IEX.NS": {
        "security_id": "220",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IGL.NS": {
        "security_id": "11262",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MGL.NS": {
        "security_id": "17534",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ADANIENSOL.NS": {
        "security_id": "10217",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "TORNTPOWER.NS": {
        "security_id": "13786",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "JSWENERGY.NS": {
        "security_id": "17869",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SUZLON.NS": {
        "security_id": "12018",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BANKINDIA.NS": {
        "security_id": "4745",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CENTRALBK.NS": {
        "security_id": "14894",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IOB.NS": {
        "security_id": "9348",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "UCOBANK.NS": {
        "security_id": "11223",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MAHABANK.NS": {
        "security_id": "11377",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "YESBANK.NS": {
        "security_id": "11915",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SBICARD.NS": {
        "security_id": "17971",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ICICIGI.NS": {
        "security_id": "21770",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "HDFCAMC.NS": {
        "security_id": "4244",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BAJAJHLDNG.NS": {
        "security_id": "305",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MFSL.NS": {
        "security_id": "2142",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CDSL.NS": {
        "security_id": "21174",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BSE.NS": {
        "security_id": "19585",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ANGELONE.NS": {
        "security_id": "324",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "360ONE.NS": {
        "security_id": "13061",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LICHSGFIN.NS": {
        "security_id": "1997",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "PNBHOUSING.NS": {
        "security_id": "18908",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "POONAWALLA.NS": {
        "security_id": "11403",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "MANAPPURAM.NS": {
        "security_id": "19061",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "COLPAL.NS": {
        "security_id": "15141",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "UNITDSPR.NS": {
        "security_id": "10447",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "VOLTAS.NS": {
        "security_id": "3718",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "CROMPTON.NS": {
        "security_id": "17094",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "DIXON.NS": {
        "security_id": "21690",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GODREJPROP.NS": {
        "security_id": "17875",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LODHA.NS": {
        "security_id": "3220",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "INDHOTEL.NS": {
        "security_id": "1512",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NYKAA.NS": {
        "security_id": "6545",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BOSCHLTD.NS": {
        "security_id": "2181",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "EXIDEIND.NS": {
        "security_id": "676",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BALKRISIND.NS": {
        "security_id": "335",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    
    "APOLLOTYRE.NS": {
        "security_id": "163",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "BHARATFORG.NS": {
        "security_id": "422",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SONACOMS.NS": {
        "security_id": "4684",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "LAURUSLABS.NS": {
        "security_id": "19234",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "IPCALAB.NS": {
        "security_id": "1633",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GLAND.NS": {
        "security_id": "1186",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "SYNGENE.NS": {
        "security_id": "10243",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "GRANULES.NS": {
        "security_id": "11872",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "AARTIIND.NS": {
        "security_id": "7",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "NAVINFLUOR.NS": {
        "security_id": "14672",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "ATUL.NS": {
        "security_id": "263",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
    "COFORGE.NS": {
        "security_id": "11543",
        "exchange_segment": "NSE_EQ",
        "instrument": "EQUITY",
    },
     "ADANITOTALGAS.NS": {
            "security_id": "6066",
            "exchange_segment": "NSE_EQ",
            "instrument": "EQUITY",
        },
     "ICICIAMC.NS": {
                 "security_id": "760407",
                 "exchange_segment": "NSE_EQ",
                 "instrument": "EQUITY",
             },
    #  "GOLDM.NS": {
    #              "security_id": "571445",
    #              "exchange_segment": "MCX_COMM",
    #              "instrument": "FUTCOM",
    #          },
    # "SILVERM.NS": {
    #             "security_id": "572773",
    #             "exchange_segment": "MCX_COMM",
    #             "instrument": "FUTCOM",
    #         },
    # "CRUDEOILM.NS": {
    #                 "security_id": "573423",
    #                 "exchange_segment": "MCX_COMM",
    #                 "instrument": "FUTCOM",
    #             },
    #  "NATURALGAS.NS": {
    #                     "security_id": "574319",
    #                     "exchange_segment": "MCX_COMM",
    #                     "instrument": "FUTCOM",
    #                 },
}

commodity={
    "GOLDM.NS": {
                     "security_id": "571445",
                     "exchange_segment": "MCX_COMM",
                     "instrument": "FUTCOM",
                 },
        "SILVERM.NS": {
                    "security_id": "572773",
                    "exchange_segment": "MCX_COMM",
                    "instrument": "FUTCOM",
                },
        "CRUDEOILM.NS": {
                        "security_id": "573423",
                        "exchange_segment": "MCX_COMM",
                        "instrument": "FUTCOM",
                    },
         "NATURALGAS.NS": {
                            "security_id": "574319",
                            "exchange_segment": "MCX_COMM",
                            "instrument": "FUTCOM",
                        },
}

# These requested tickers were not found as NSE EQ-series equity rows in the uploaded CSV.
MISSING_FROM_UPLOADED_MASTER = [
    "LTIM.NS",
    "PEL.NS",
    "REC.NS",
    "TATAMOTORS.NS",
    "ADANITOTALGAS.NS",
    "ICICIPRULI.NS",
]
