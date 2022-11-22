import pandas as pd
import sqlite3
import ccxt
import requests

quote = "BTC"

#Binance 所有現貨ＢＴＣ交易對
exchange = ccxt.binance()
market = exchange.load_markets()


# 計算每個幣的市值
# https://stackoverflow.com/questions/66132843/is-there-a-way-to-get-the-market-cap-or-market-cap-rank-of-a-coin-using-the-bina

#取得市值資料
def get_market_cap():

    re = requests.get("https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products")
    data = re.json()
    data = data["data"]

    all_symbols = [ (i["s"],float(i["cs"])*float(i["c"])) for i in data if i["q"] == "USDT" and\
                                i["st"] == "TRADING" and\
                                i["c"] != None and\
                                i["cs"] != 0 and\
                                i["cs"] != None ]  

    all_symbols =  sorted(all_symbols, key=lambda s:s[1], reverse=True) 

    return [i[0] for i in all_symbols]    #排序市值   

symbol_list = get_market_cap()  


conn = sqlite3.connect("ttt.db")
curosor = conn.cursor()

coindata = exchange.fetch_ohlcv("BTCUSDT",timeframe="15m", limit=200)

