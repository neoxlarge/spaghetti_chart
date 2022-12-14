import sqlite3
import datetime as dt
import pandas as pd
import plotly.graph_objects as px
import logging
import dash
from dash import dcc
from dash import html
#pip install dash-bootstrap-components
import dash_bootstrap_components as dbc

dash.register_page(__name__,path="/")

#general setting
dbfile = "coin.db"
table_name = "coin_table"
#@markdown 依BTC或USDT交易對為準
quote = "BTC" #@param ["BTC", "USDT"]
#@markdown 依市值分區
divide = 5 #@param {type:"slider", min:1, max:5, step:1}

tags = ('Metaverse', 'newListing', 'Launchpool', 'NFT', 'pow', 'Layer1_Layer2', 
    'defi', 'Gaming', 'fan_token', 'BSC', 'Launchpad', 
    'storage-zone', 'Polkadot', 'Infrastructure', 'bnbchain', 'innovation-zone', 'pos', 'mining-zone')


# setting logging
logformat = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")

mylog = logging.Logger("mylog")
mylog.setLevel(logging.INFO)

filehandle = logging.FileHandler("mylog.log")
filehandle.setLevel(logging.INFO)
filehandle.setFormatter(logformat)

streamhandle = logging.StreamHandler()
streamhandle.setLevel(logging.INFO)
streamhandle.setFormatter(logformat)

mylog.addHandler(filehandle)
mylog.addHandler(streamhandle)

def df_from_database(db,table,symbol_list):
    """
    get data from local sqlite database
    db: database file name
    table: table name in the database.
    symbol_list: symbol list
    """
    
    #bug
    #1INCH可能造成查詢sql出問題, 可以用'號包起來解, 但先把1INCH拿掉,待解.
    conn = sqlite3.connect(db)
    #symbol_list = [f"'{i}'" for i in symbol_list]
    
    list_string = ",".join(symbol_list)
    
    sql_string = f"select * from (select Timestamp,{list_string} from {table} order by Timestamp desc limit 200) order by Timestamp"
    print(sql_string)
    data_df = pd.read_sql_query(sql_string,con=conn)
    mylog.info(sql_string)

    data_df["Timestamp"] = pd.to_datetime(data_df["Timestamp"],unit="ms",utc=True).map(lambda x: x.tz_convert('Asia/Taipei'))
    data_df.set_index("Timestamp",inplace=True)
    
    return data_df
    


def group_by_market_cap(data_list,divide):
    """依市值分類
    傳入所有幣種資料,和要分幾區.
    回傳分類好的dict.    
    """
    market_cap_data = {i["s"] : float(i["cs"]) * float(i["c"]) for i in data_list if i["q"] == quote and\
                                        i["st"] == "TRADING" and\
                                        i["c"] != None and\
                                        i["cs"] != 0 and\
                                        i["cs"] != None and\
                                        i["b"] != "1INCH"    }

    market_cap_data = sorted(market_cap_data.items(),key=lambda d: d[1],reverse=True)

    market_cap_data = [i[0] for i in market_cap_data]

    section = len(market_cap_data) // divide
    part=1
    result = dict()
    while len(market_cap_data) > 0:
        result[f"Market_cap_part{part}"] = market_cap_data[0:section+1]
        market_cap_data = market_cap_data[section+1:]
        part = part + 1
        
    return result    

def group_by_category(data_list,category):
    """依板塊分類
    傳入所有幣種資料,和板塊分類.
    回傳分類好的dict.   
    """
    
    group_list=dict()
    for c_index in category:

        group = [i["s"] for i in data_list if i["q"] == quote and\
                                c_index in i["tags"] and\
                                i["st"] == "TRADING" and\
                                i["c"] != None and\
                                i["cs"] != 0 and\
                                i["cs"] != None and\
                                i["b"] != "1INCH"   ]
        group_list[c_index] = group                        

    return group_list                        

def get_binance_all_symbol():
    """ 
    取得Binance幣種資料
    參考連結
    計算每個幣的市值
    https://stackoverflow.com/questions/66132843/is-there-a-way-to-get-the-market-cap-or-market-cap-rank-of-a-coin-using-the-bina
   
    """
    import requests
    re = requests.get("https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products")
    data = re.json()
    return data["data"]

def plotly_sc(data_df,title_text):
    px_list = list()
    html_list = list()
    for i,key in enumerate(data_df):
        _ = px.Scatter(
            x=data_df.index,
            y=data_df[key],
            name=f"{key}",
            mode="lines",
            line=dict(width=1))
        
        px_list.append(_)

    lastrow = data_df.iloc[-1]

    label_text = px.Scatter(
            x=[lastrow.name + dt.timedelta(minutes=180) for i in lastrow],
            y=lastrow.values,
            mode="text",
            marker=(dict(symbol="arrow-left",size=20)),
            text=[ f"{i} {lastrow[i]:.2f}%" for i in lastrow.keys()],
            textposition="middle center")
    
    fig = px.Figure()
    fig["layout"]["template"]="plotly_dark"
    fig.update_layout(showlegend=False,title=title_text,autosize=True)
    #fig.update_layout(showlegend=False,title=title_text,width=1200,height=600)
    fig.add_traces(px_list)
    fig.add_trace(label_text)
        
    return fig


def convent2_pecentage_df(data_df):
    """
    傳入dataframe,以第0 row為準, 轉成是第0row的%數
    """
    #pct_df = pd.DataFrame(data_df.get("Close"))

    pct_df = data_df
    base = pct_df.iloc[0]
    
    for i,key in enumerate(pct_df):
       pct_df[key] = pct_df[key].apply(lambda x : ((x - base[key]) / base[key] * 100))
    
    return pct_df



    #1. get binance all symbol
all_symbol = get_binance_all_symbol()

    #2. 取得的all symbol,依市值分區.
market_cap_group = group_by_market_cap(all_symbol,divide)
    

    #3. 取得的all symbol, 依版塊分區.
category_group = group_by_category(all_symbol,tags)

#合併
market_cap_group.update(category_group)
all_group = market_cap_group
all_group_radioitems = [ i for i in all_group.keys()]

radioitems = dcc.RadioItems(options = all_group_radioitems, value = all_group_radioitems[0],
id="selected_item",style={"display":"inline-block","margin": "auto"})
figx = dcc.Graph(id = "fig1_out")

layout = html.Div([
    html.H5("coin price changes in Binance BTC pairs"),
    dcc.Interval(id='interval-component',
            interval=15*60*1000, # in milliseconds
            n_intervals=0),
    radioitems,
    figx,
])

@dash.callback(
    dash.Output(component_id="fig1_out",component_property="figure"),
    [dash.Input(component_id="selected_item",component_property="value"),
    dash.Input('interval-component', "n_intervals")]
  )
def update_fig(input_value1,input_value2):
    
    dbdata_df = df_from_database(dbfile,table_name,all_group[input_value1])
    spaghetti_df = convent2_pecentage_df(dbdata_df)
    title_text = f"{input_value1}   timeframe:15m   last upate:{dbdata_df.index[-1] }"
    fig1 = plotly_sc(spaghetti_df,title_text)
    return fig1



#app.run_server(port = 8080, host='0.0.0.0')