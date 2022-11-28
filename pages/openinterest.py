import ccxt
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

dash.register_page(__name__,path="/oi")

#general setting
dbfile = "coin.db"
table_name = "oi_table"
#@markdown 依市值分區
divide = 5 #@param {type:"slider", min:1, max:5, step:1}

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
     
    conn = sqlite3.connect(db)
        
    list_string = ",".join(symbol_list)
    
    sql_string = f"select * from (select Timestamp,{list_string} from {table} order by Timestamp desc limit 200) order by Timestamp"
    print(sql_string)
    data_df = pd.read_sql_query(sql_string,con=conn)
    mylog.info(sql_string)

    data_df["Timestamp"] = pd.to_datetime(data_df["Timestamp"],unit="ms",utc=True).map(lambda x: x.tz_convert('Asia/Taipei'))
    data_df.set_index("Timestamp",inplace=True)
    
    return data_df
    


def group_by_oi(data_list,divide):
    """OI分區
    傳入要分幾區.
    回傳分類好的dict.    
    """
    section = len(data_list) // divide
    part=1
    result = dict()
    while len(data_list) > 0:
        result[f"oi_part{part}"] = data_list[0:section+1]
        data_list = data_list[section+1:]
        part = part + 1
        
    return result    


def get_binance_perp_symbol():
    #binance　所有永續合約(USDT)交易對
    exchange_perp = ccxt.binanceusdm()
    market_perp = exchange_perp.load_markets()

    perp_list = [market_perp[i]["id"] for i in market_perp if market_perp[i]["quote"] == "USDT" and\
                            market_perp[i]["type"] == "future" and\
                            market_perp[i]["active"] == True and\
                            market_perp[i]["expiry"] == None and\
                            market_perp[i]["id"] not in ["1INCHUSDT","1000SHIBUSDT","1000XECUSDT","1000LUNCUSDT"]]

   #bug
    #1INCH可能造成查詢sql出問題, 可以用'號包起來解, 但先把1INCH拿掉,待解.
    return perp_list



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
all_symbol = get_binance_perp_symbol()

    #2. 取得的all symbol,oi分區.
oi_group = group_by_oi(all_symbol,divide)
    
all_group_radioitems = [ i for i in oi_group.keys()]

radioitems = dcc.RadioItems(options = all_group_radioitems, value = all_group_radioitems[0],
id="selected_oi_item",style={"display":"inline-block","margin": "auto"})
fig_oi = dcc.Graph(id = "fig_oi_out")

layout = html.Div([
    html.H5("oi changes in Binance USDⓈ-M Futures"),
    dcc.Interval(id='interval-component',
            interval=15*60*1000, # in milliseconds
            n_intervals=0),
    radioitems,
    fig_oi,
])

@dash.callback(
    dash.Output(component_id="fig_oi_out",component_property="figure"),
    [dash.Input(component_id="selected_oi_item",component_property="value"),
    dash.Input(component_id='interval-component', component_property= "n_intervals")]
  )
def update_fig(input_value1,input_value2):
    
    dbdata_df = df_from_database(dbfile,table_name,oi_group[input_value1])
    print(input_value1)
    spaghetti_df = convent2_pecentage_df(dbdata_df)
    title_text = f"{input_value1}   timeframe:15m   last upate:{dbdata_df.index[-1] }"
    fig2 = plotly_sc(spaghetti_df,title_text)
    return fig2



#app.run_server(port = 8080, host='0.0.0.0')