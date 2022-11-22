import ccxt
import schedule
import logging
import pandas as pd
import sqlite3
import ccxt
import requests
import datetime as dt
import time

default_logger = logging.getLogger()
default_logger.setLevel(logging.INFO)
logformat = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")
default_logger.handlers[0].setFormatter(logformat)




#setting

dbfile = "coin.db"
table_name = "coin_table"
quote = "BTC"



#Binance 所有現貨ＢＴＣ交易對
exchange = ccxt.binance()
market = exchange.load_markets()


# 計算每個幣的市值
# https://stackoverflow.com/questions/66132843/is-there-a-way-to-get-the-market-cap-or-market-cap-rank-of-a-coin-using-the-bina

#取得sybol清單並以市值資料排序
def get_market_cap(quote="BTC"):

    re = requests.get("https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products")
    data = re.json()
    data = data["data"]

    all_symbols = [ (i["s"],float(i["cs"])*float(i["c"])) for i in data if i["q"] == quote and\
                                i["st"] == "TRADING" and\
                                i["c"] != None and\
                                i["cs"] != 0 and\
                                i["cs"] != None ]  

    all_symbols =  sorted(all_symbols, key=lambda s:s[1], reverse=True) 

    return [i[0] for i in all_symbols]    #排序市值   

symbol_list = get_market_cap()  


def update_database():
    #connect database
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()

    #check table exists
    check_table = cursor.execute(f"select count(*) from sqlite_master where type = 'table' and name = '{table_name}'")
    table_exists = check_table.fetchone()[0] > 0

    #if table in not exists then create it.
    if table_exists == False:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name}(Timestamp INTEGER PRIMARY KEY)")
        conn.commit()

    last_record = cursor.execute(f"select Timestamp from {table_name} order by Timestamp desc limit 1")
    last_record = last_record.fetchall()
    logging.info(f"last record timestamp: {last_record}" )

    if last_record == []:
        start_timestamp = dt.datetime.now() - dt.timedelta(days=3)
        start_timestamp = int(start_timestamp.timestamp()*1000)
    else: 
        start_timestamp = last_record[0][0]    

    logging.info(f"star timestamp: {start_timestamp}")



    coindata = exchange.fetch_ohlcv(symbol="BTCUSDT", timeframe = "15m",since=start_timestamp)
    coindata = [ (i[0],) for i in coindata]
    coindata = coindata[1:]
    insert_sql = f"insert into {table_name} (Timestamp) values (?)"
    cursor.executemany(insert_sql,coindata)
    conn.commit()

    check_column = cursor.execute(f"select sql from sqlite_master")
    check_column = check_column.fetchall()[0][0]
    check_column = check_column[check_column.find("KEY,")+4:-1]
    check_column = check_column.replace("real","").replace("' ","").replace(" '","").split(",")

    for symbol in symbol_list:
        logging.info(f"{symbol} is downloading.")
        coindata = exchange.fetch_ohlcv(symbol=symbol, timeframe = "15m", since=start_timestamp)
        coindata = [ (i[4],i[0]) for i in coindata]

        if symbol not in check_column:
            cursor.execute(f"alter table '{table_name}' add column '{symbol}' real")
            conn.commit()

        update_sql = f"update '{table_name}' set '{symbol}' = ? where Timestamp = ?"
        cursor.executemany(update_sql,coindata)
        conn.commit()

    conn.close()



def sche():

    logging.info("schedule download...")
    update_database()

schedule.every().hour.at(":01").do(sche)    
schedule.every().hour.at(":16").do(sche)
schedule.every().hour.at(":31").do(sche)  
schedule.every().hour.at(":46").do(sche)      

while True:
    schedule.run_pending()
    time.sleep(1)