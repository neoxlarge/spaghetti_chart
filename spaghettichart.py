import vectorbt as bt
import binance



#@title 預設標題文字
#@markdown 依BTC或USDT交易對為準
quote = "BTC" #@param ["BTC", "USDT"]
#@markdown 資料天數及時框
days = 2 #@param {type:"slider", min:1, max:30, step:1}
timeframe = "15m" #@param ["15m", "1h", "4h"]
#@markdown 依市值分區
divide = 5 #@param {type:"slider", min:1, max:5, step:1}

tags = ('Metaverse', 'newListing', 'Launchpool', 'NFT', 'pow', 'Layer1_Layer2', 
    'defi', 'Gaming', 'fan_token', 'BSC', 'Launchpad', 
    'storage-zone', 'Polkadot', 'Infrastructure', 'bnbchain', 'innovation-zone', 'pos', 'mining-zone')



def group_by_market_cap(data_list,divide):
    """依市值分類"""

    market_cap_data = {i["s"] : float(i["cs"]) * float(i["c"]) for i in data_list if i["q"] == quote and\
                                        i["st"] == "TRADING" and\
                                        i["c"] != None and\
                                        i["cs"] != 0 and\
                                        i["cs"] != None}

    market_cap_data = sorted(market_cap_data.items(),key=lambda d: d[1],reverse=True)

    market_cap_data = [i[0] for i in market_cap_data]

    section = len(market_cap_data) // divide
    part=1
    result = dict()
    while len(market_cap_data) > 0:
        result[f"Market_cap_part{part}"] = market_cap_data[0:section+1]
        #result.append(data_list[0:section+1])
        market_cap_data = market_cap_data[section+1:]
        part = part + 1
        
    return result    



def group_by_category(data_list,category):
    """依板塊分類"""
    
    group_list=dict()
    for c_index in category:

        group = [i["s"] for i in data_list if i["q"] == quote and\
                                c_index in i["tags"] and\
                                i["st"] == "TRADING" and\
                                i["c"] != None and\
                                i["cs"] != 0 and\
                                i["cs"] != None]
        group_list[c_index] = group                        

    return group_list                        


import vectorbt as vbt
import datetime as dt
import pandas as pd
import plotly.graph_objects as px

def download_data(data_list):
    start_date = dt.datetime.now() - dt.timedelta(days=days)
    end_date = dt.datetime.now()

    download_data = vbt.BinanceData.download(
    data_list,
    start = start_date,
    end = end_date,
    interval=timeframe,
    )
    return download_data


def convent2_pecentage_df(data_df):
    pct_df = pd.DataFrame(data_df.get("Close"))
    base = pct_df.iloc[0]
    
    for i,key in enumerate(pct_df):
       pct_df[key] = pct_df[key].apply(lambda x : ((x - base[key]) / base[key] * 100))
    
    return pct_df



    

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
            x=[lastrow.name + dt.timedelta(minutes=60) for i in lastrow],
            y=lastrow.values,
            mode="text",
            marker=(dict(symbol="arrow-left",size=20)),
            text=[ f"{i} {lastrow[i]:.2f}%" for i in lastrow.keys()],
            textposition="middle center")
    
    fig = px.Figure()
    fig["layout"]["template"]="plotly_dark"
    fig.update_layout(showlegend=False,title=title_text,width=1200,height=600)
    fig.add_traces(px_list)
    fig.add_trace(label_text)
    #fig.write_html(f"{title_text}.html")
    
    #fig.show()
    return fig

#下載全部幣的資料約5分鐘

# 計算每個幣的市值
# https://stackoverflow.com/questions/66132843/is-there-a-way-to-get-the-market-cap-or-market-cap-rank-of-a-coin-using-the-bina

#取得市值資料
import requests
re = requests.get("https://www.binance.com/exchange-api/v2/public/asset-service/product/get-products")
data = re.json()
data = data["data"]

all_symbols = [ i["s"] for i in data if i["q"] == quote and\
                            i["st"] == "TRADING" and\
                            i["c"] != None and\
                            i["cs"] != 0 and\
                            i["cs"] != None ]  

market_cap_group = group_by_market_cap(data,divide)

category_group = group_by_category(data,tags)

market_cap_group.update(category_group)
all_group = market_cap_group

#download data
dw_data = download_data(all_symbols)


#convent to pencentage dataframe
spaghetti_df = convent2_pecentage_df(dw_data)



#plotly_sc(spaghetti_df[all_group["Market_cap_part1"]],"Market_cap_part1")


import dash
from dash import dcc
from dash import html

fig1 = plotly_sc(spaghetti_df[all_group["Market_cap_part1"]],"Market_cap_part1")

app = dash.Dash(__name__)

app.layout = html.Div(

children = [
     dcc.Graph(
         figure = fig1)]
)

if __name__ == "__main__":
    app.run_server(debug=True)