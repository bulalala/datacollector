# -*- coding: utf-8 -*-
from datetime import datetime
from dbWrapper import dbWrapper
import pandas as pd
import pyecharts.echarts.events as events
from pyecharts import Bar
from pyecharts_javascripthon.dom import alert
from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtCore import pyqtSignal,QObject,QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from eventEngine import *
import sys
import os


db = dbWrapper('postgres-fj7nqbmu.sql.tencentcdb.com')


def color_function(params):
    if params.value > 0:
        return '#FF4500'
    else:
        return '#54ffff'

def on_click():
    alert("点击事件触发")

class Communicate(QObject):
    emitButton = pyqtSignal(float)

class SpreadWidget(QtGui.QWidget,object):
    Signal = QtCore.pyqtSignal()
    #----------------------------------------------------------------------
    def __init__(self,eventEngine,parent=None):
        """Constructor"""
        self.parent = parent
        QtGui.QWidget.__init__(self, parent)
        self.eventEngine = eventEngine
        self.eventEngine.start()
        self.eventEngine.register("showData", self.showData)
        self.web_view = QWebEngineView()
        if not (os.path.exists('./html')):
            print('no!!!')
            os.makedirs('./html')
        self.url_string = "file:///./html/spread.html"
        self.web_view.load(QUrl(self.url_string))

        self.label_date = QtWidgets.QLabel(self)
        self.label_date.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label_date.setFixedSize(40, 35)
        self.label_date.setObjectName("label_date")
        self.label_date.setText(U"日期")
        self.label_long = QtWidgets.QLabel(self)
        self.label_long.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label_long.setFixedSize(60, 35)
        self.label_long.setObjectName("label_long")
        self.label_long.setText(U"第一腿")
        self.label_short = QtWidgets.QLabel(self)
        self.label_short.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label_short.setFixedSize(60, 35)
        self.label_short.setObjectName("label_short")
        self.label_short.setText(U"第二腿")
        self.cbb_date = QtWidgets.QComboBox(self)
        self.cbb_date.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.cbb_date.setFixedSize(180, 35)
        self.cbb_date.setObjectName("cbb_date")
        self.btn_load = QtWidgets.QPushButton(U'分析', self)
        self.btn_load.setGeometry(QtCore.QRect(242, 0, 81, 25))
        self.btn_load.setFixedSize(80, 35)
        self.btn_load.setObjectName("btn_load")
        self.btn_load.clicked.connect(self.clickedbutton)
        self.lineEdit_long = QtWidgets.QLineEdit(self)
        self.lineEdit_long.setGeometry(QtCore.QRect(210, 70, 181, 111))
        self.lineEdit_long.setObjectName("lineEdit_long")
        self.lineEdit_short = QtWidgets.QLineEdit(self)
        self.lineEdit_short.setGeometry(QtCore.QRect(210, 70, 181, 111))
        self.lineEdit_short.setObjectName("lineEdit_short")
        self.vb_fistline = QtGui.QHBoxLayout()
        self.vb_fistline.addWidget(self.label_date)
        self.vb_fistline.addWidget(self.cbb_date)
        self.vb_fistline.addWidget(self.label_long)
        self.vb_fistline.addWidget(self.lineEdit_long)
        self.vb_fistline.addWidget(self.label_short)
        self.vb_fistline.addWidget(self.lineEdit_short)
        self.vb_fistline.addWidget(self.btn_load)
        self.vb_fistline.addStretch(2)
        self.hb = QtGui.QHBoxLayout()
        self.hb.addWidget(self.web_view)
        self.lastb = QtGui.QVBoxLayout()
        self.lastb.addLayout(self.vb_fistline)
        self.lastb.addLayout(self.hb)
        self.setLayout(self.lastb)
        self.web_view.show()
        self.tradingdays = db.getOpenIntTradingDay()
        self.initModel()
        self.c = Communicate()
        self.c.emitButton.connect(self.emitSignal)

    def clickedbutton(self):
        event = Event("showData")
        self.eventEngine.put(event)
        return

    def initModel(self):
        for i in range(len(self.tradingdays)-1,1,-1):
            self.cbb_date.addItem(self.tradingdays.loc[i,'tradingday'])

    def showData(self, event):
        print('test')
        cur_tradingday = self.cbb_date.currentText()
        symbol_long = self.lineEdit_long.text()
        symbol_short = self.lineEdit_short.text()
        print(symbol_long)
        self.loadhtml(cur_tradingday,symbol_long,symbol_short)
        self.c.emitButton.emit(0.1)
        return

    def loadhtml(self,tradingday,symbol_long,symbol_short):
        data = db.getDataByTradingday(tradingday)
        data_1 = data[data.symbol == symbol_long]
        data_2 = data[data.symbol == symbol_short]
        if len(data_1) == 0 or len(data_2) == 0:
            print('no datas')
            return
        data_1 = data_1[['symbol', 'company', 'quatity']]
        data_2 = data_2[['symbol', 'company', 'quatity']]
        df = pd.merge(data_1, data_2, on='company', how='inner')
        df['director'] = df['quatity_x'] * df['quatity_y']
        x = []
        y = []
        for i in range(0, len(df)):
            if df.loc[i, 'quatity_x'] > 0 and df.loc[i, 'quatity_y'] < 0:
                qty = min(abs(df.loc[i, 'quatity_x']), abs(df.loc[i, 'quatity_y']))
                str = 'buy ' + symbol_long + ' sell ' + symbol_short
                a = [df.loc[i, 'company'], qty, str]
                x.append(a)
            elif df.loc[i, 'quatity_x'] < 0 and df.loc[i, 'quatity_y'] > 0:
                qty = min(abs(df.loc[i, 'quatity_x']), abs(df.loc[i, 'quatity_y']))
                str = 'sell ' + symbol_long + ' buy ' + symbol_short
                a = [df.loc[i, 'company'], qty, str]
                y.append(a)
        rst_long = pd.DataFrame(x)
        rst_short = pd.DataFrame(y)
        if len(rst_long) > 0:
            rst_long.columns = ['company', 'qty', 'title']
            rst_long = rst_long.sort_values(by='qty', ascending=True)
        if len(rst_short) > 0:
            rst_short.columns = ['company', 'qty', 'title']
            rst_short[['qty']] = -rst_short[['qty']]
            rst_short = rst_short.sort_values(by='qty', ascending=False)

        df = pd.DataFrame()
        df = df.append(rst_short)
        df = df.append(rst_long)
        print(df)
        print(df['qty'].values.tolist())
        title = 'sp:{}/{}({})'.format(symbol_long, symbol_short,tradingday)
        bar = Bar(title)
        bar.use_theme('macarons')
        if len(df) > 0:
            bar.add("持仓量", df['company'].values.tolist(), df['qty'].values.tolist(), is_convert=True, mark_point=["max", "min"])
        else:
            bar.add("持仓量", [], [], is_convert=True)
        bar._option['series'][0]['itemStyle'] = {
            'normal': {
                'color': color_function,
            }
        }
        #bar.on(events.MOUSE_CLICK, on_click)
        bar.render('./html/spread.html')

    def emitSignal(self, p):
        self.web_view.load(QUrl(self.url_string))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ee = EventEngine()
    ui = SpreadWidget(ee)
    ui.showMaximized()
    app.exec_()