import ccxt
import schedule
import logging
import sqlite3
import requests
import datetime as dt
import time


# setting logging
logformat = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")

mylog = logging.Logger("mylog")
mylog.setLevel(logging.INFO)

filehandle = logging.FileHandler("mylog.log",mode="w")
filehandle.setLevel(logging.INFO)
filehandle.setFormatter(logformat)

streamhandle = logging.StreamHandler()
streamhandle.setLevel(logging.INFO)
streamhandle.setFormatter(logformat)

mylog.addHandler(filehandle)
mylog.addHandler(streamhandle)

#setting

dbfile = "coin.db"
table_name = "coin_table"
oi_table_name = "oi_table"
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

#binance　所有永續合約(USDT)交易對
exchange_perp = ccxt.binanceusdm()
market_perp = exchange_perp.load_markets()

perp_list = [market_perp[i]["id"] for i in market_perp if market_perp[i]["quote"] == "USDT" and\
                        market_perp[i]["type"] == "future" and\
                        market_perp[i]["active"] == True and\
                        market_perp[i]["expiry"] == None]



def update_database(symbol_list,dbfile,table_name,chart_type):
    """
    symbol_list = ["BTC/USDT","ETHUSDT"],
    dbfile = database file name.
    talble_name = table name in the database.
    chart_type = price or oi
    """
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
    
    #取得最後一筆記錄的timestamp, 抓資料時會以這筆為開頭.
    #最後一筆資料為未收線的資料, 須要被覆蓋掉.
    last_record = cursor.execute(f"select Timestamp from {table_name} order by Timestamp desc limit 1")
    last_record = last_record.fetchall()
    mylog.info(f"last record timestamp: {last_record}" )

    if last_record == []:
        start_timestamp = dt.datetime.now() - dt.timedelta(days=3)
        start_timestamp = int(start_timestamp.timestamp()*1000)
    else: 
        start_timestamp = last_record[0][0]    

    mylog.info(f"star timestamp: {start_timestamp}")


    coindata = exchange.fetch_ohlcv(symbol="BTCUSDT", timeframe = "15m",since=start_timestamp)
    coindata = [ (i[0],) for i in coindata]
    coindata = coindata[1:]
    #先把primay key 先insert into到table, 剩下的格子可以用update的.
    insert_sql = f"insert into {table_name} (Timestamp) values (?)"
    cursor.executemany(insert_sql,coindata)
    conn.commit()

    #檢查symbol是否有己存在次欄位,沒有就新增該欄位.
    check_column = cursor.execute(f"select sql from sqlite_master where tbl_name = '{table_name}'")
    check_column = check_column.fetchall()[0][0]
    check_column = check_column[check_column.find("KEY,")+4:-1]
    check_column = check_column.replace("real","").replace("' ","").replace(" '","").split(",")

    if chart_type == "price":
        for symbol in symbol_list:
            mylog.info(f"{symbol} price is downloading.")
            coindata = exchange.fetch_ohlcv(symbol=symbol, timeframe = "15m", since=start_timestamp)
            coindata = [ (i[4],i[0]) for i in coindata] #("Close","Timestamp")

            if symbol not in check_column:
                cursor.execute(f"alter table '{table_name}' add column '{symbol}' real")
                conn.commit()

            update_sql = f"update '{table_name}' set '{symbol}' = ? where Timestamp = ?"
            cursor.executemany(update_sql,coindata)
            conn.commit()

    elif chart_type == "oi":
        for symbol in symbol_list:
            mylog.info(f"{symbol} oi is downloading.")
            oidata = exchange_perp.fetch_open_interest_history(symbol=symbol, timeframe = "15m", since=start_timestamp,limit=300)  #要加limit,不然只會有30個資料. 原因不明.
            oidata = [(i["baseVolume"],i["timestamp"]) for i in oidata]
            
            if symbol not in check_column:
                cursor.execute(f"alter table '{table_name}' add column '{symbol}' real")
                conn.commit()

            update_sql = f"update '{table_name}' set '{symbol}' = ? where Timestamp = ?"
            cursor.executemany(update_sql,oidata)
            conn.commit()

    else: 

        raise Exception("chart_type wrong! must be 'price' or 'oi'.")            

    conn.close()


def main():
    def sche():

        mylog.info("schedule download...")
        update_database(symbol_list=symbol_list,dbfile=dbfile, table_name=table_name,chart_type="price")
        update_database(symbol_list=perp_list,dbfile=dbfile, table_name=oi_table_name,chart_type="oi")

    schedule.every().hour.at(":01").do(sche)    
    schedule.every().hour.at(":16").do(sche)
    schedule.every().hour.at(":31").do(sche)  
    schedule.every().hour.at(":46").do(sche)      

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()        