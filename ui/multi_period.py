# -*- coding: utf-8 -*-
from datetime import datetime
from dbWrapper import dbWrapper
import pandas as pd
from pyecharts import Bar
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

db = dbWrapper('postgres-a1mzuj9c.sql.tencentcdb.com')
data = db.getDataByTradingday('20181022')
symbol1 = 'FG901'
symbol2 = 'FG905'
data_1 = data[data.symbol == symbol1]
data_2 = data[data.symbol == symbol2]
data_1 = data_1[['symbol','company','quatity']]
data_2 = data_2[['symbol','company','quatity']]
df = pd.merge(data_1,data_2,on='company',how='inner')
df['director'] = df['quatity_x']*df['quatity_y']
multi_data = pd.DataFrame()
x = []
y = []
for i in range(0,len(df)):
    if df.loc[i,'quatity_x'] > 0 and df.loc[i,'quatity_y'] < 0:
        qty = min(abs(df.loc[i,'quatity_x']),abs(df.loc[i,'quatity_y']))
        str = 'buy '+symbol1+' sell '+symbol2
        a = [df.loc[i,'company'],qty,str]
        x.append(a)
    elif df.loc[i,'quatity_x'] < 0 and df.loc[i,'quatity_y'] > 0:
        qty = min(abs(df.loc[i,'quatity_x']),abs(df.loc[i,'quatity_y']))
        str = 'sell '+symbol1+' buy '+symbol2
        a = [df.loc[i,'company'],qty,str]
        y.append(a)
rst_long = pd.DataFrame(x)
rst_short = pd.DataFrame(y)
if len(rst_long) > 0:
    rst_long.columns = ['company','qty','title']
    rst_long = rst_long.sort_values(by='qty',ascending=True)
if len(rst_short) > 0:
    rst_short.columns = ['company','qty','title']
    rst_short[['qty']] = -rst_short[['qty']]
    rst_short = rst_short.sort_values(by='qty',ascending=False)

# df = pd.DataFrame()
# df.append(rst_long)
# df.append(rst_short)
# print(df)
df = pd.DataFrame()
df = df.append(rst_short)
df = df.append(rst_long)
print(df)
print(df['qty'].values.tolist())
title = 'sp:{}/{}'.format(symbol1,symbol2)
bar = Bar(title)
if len(df) > 0:
    bar.add("持仓量", df['company'].values.tolist(), df['qty'].values.tolist(),is_convert=True)
else:
    bar.add("持仓量",[], [], is_convert=True)
bar.render('./html/spread.html')

app = QApplication([])
view = QWebEngineView()
url_string = "file:///./html/spread.html"
view.load(QUrl(url_string))
view.show()
app.exec_()



