# encoding: UTF-8
__author__ = 'hyc'

import sys
import pandas as pd
import numpy as np
#自己开发模块
from dbWrapper import dbWrapper
from structureWidget import StructWidget

from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtCore import pyqtSignal,QObject
import pyqtgraph as pg
from eventEngine import *
import sip

db = dbWrapper('postgres-fj7nqbmu.sql.tencentcdb.com')

def plotLineGraphItem(name,lstX=[],lstY=[],lstZ=[],lstU=[],lstW=[]):
        p = pg.PlotItem(title=name)
        p.addLegend()
        if len(lstX)==0:
            return p
        i = 0
        ix = []
        ticklist = []
        for x in lstX:
            ix.append(i)
            ticklist.append((i, x))
            if lstY[i] > 0:
                k = 0.5
            else:
                k = 0
            text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">'+ "%.1f"%(lstY[i]) + '</span><br></div>', anchor=(0.5,k), angle=0)
            p.addItem(text)
            text.setPos(i,lstY[i])
            i = i + 1
        p.plot(ix, lstY, symbol='o',symbolBrush=(255,0,0),pen=(255,0,0),name="today")
        p.plot(ix, lstZ, symbol='o',symbolBrush=(0,255,0),pen=(0,255,0),name="1d")
        p.plot(ix, lstU, symbol='o',symbolBrush=(255,255,0),pen=(255,255,0),name="1w")
        p.plot(ix, lstW, symbol='o',symbolBrush=(0,0,255),pen=(0,0,255),name="1m")
        p.setXRange(-1, i-1)
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p

def plotLineSpreadItem(name,dfBar):
        p = pg.PlotItem(title=name)
        p.addLegend()
        if len(dfBar)==0:
            return p
        p.plot(range(0,len(dfBar)), dfBar['spread'].values.tolist(),pen=(255,0,0))
        ticklist = []
        ticklist.append((0,dfBar.iat[0,0]))
        ticklist.append((len(dfBar)-1,dfBar.iat[len(dfBar)-1,0]))
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p

def getDatas(productid,tradingday):
    dfbars = pd.DataFrame()
    dfstd = pd.DataFrame()
    symbol = db.getTradeSymbol_productid(productid,tradingday)
    colname = ['tradingay']
    symbols = symbol['symbol'].values.tolist()
    for sym in symbol['symbol']:
        colname.append(sym)
        bar = db.getBarsbyDay(sym)
        bar['std'] = pd.rolling_std(bar['closeprice'],20)
        if len(dfbars) == 0:
            dfbars = bar[['tradingday','closeprice']]
            dfstd = bar[['tradingday','std']]
        else:
            dfbars = pd.merge(dfbars,bar[['tradingday','closeprice']],on='tradingday',how='outer')
            dfstd = pd.merge(dfstd,bar[['tradingday','std']],on='tradingday',how='outer')
    dfbars = dfbars.sort_values(['tradingday'],ascending = True)
    dfbars.index = range(0,len(dfbars))

    dfstd = dfstd.sort_values(['tradingday'],ascending = True)
    dfstd.index = range(0,len(dfstd))

    dfbars.columns = colname
    dfstd.columns = colname
    lstX = symbols
    index = dfbars.index.values
    lstY = dfbars[symbols].loc[index.tolist()[-1]].values.tolist()
    lstZ = dfbars[symbols].loc[index.tolist()[-2]].values.tolist()
    lstU = dfbars[symbols].loc[index.tolist()[-7]].values.tolist()
    lstW = dfbars[symbols].loc[index.tolist()[-20]].values.tolist()
    p1 = plotLineGraphItem(productid+U"-价格",lstX,lstY,lstZ,lstU,lstW)

    lstY = dfstd[symbols].loc[index.tolist()[-1]].values.tolist()
    lstZ = dfstd[symbols].loc[index.tolist()[-2]].values.tolist()
    lstU = dfstd[symbols].loc[index.tolist()[-7]].values.tolist()
    lstW = dfstd[symbols].loc[index.tolist()[-20]].values.tolist()
    p2 = plotLineGraphItem(productid+U"-波动率",lstX,lstY,lstZ,lstU,lstW)
    return p1,p2

def getDatabySymbol(lstSymbol,productid):
    dfbars = pd.DataFrame()
    colname = ['tradingay']
    for sym in lstSymbol:
        colname.append(sym)
        bar = db.getBarsbyDay(sym)
        bar['std'] = pd.rolling_std(bar['closeprice'],20)
        if len(dfbars) == 0:
            dfbars = bar[['tradingday','closeprice']]
            dfstd = bar[['tradingday','std']]
        else:
            dfbars = pd.merge(dfbars,bar[['tradingday','closeprice']],on='tradingday',how='outer')
            dfstd = pd.merge(dfstd,bar[['tradingday','std']],on='tradingday',how='outer')
    dfbars.columns = colname
    dfstd.columns = colname
    lstX = lstSymbol
    index = dfbars.index.values
    lstY = dfbars[lstSymbol].loc[index.tolist()[-1]].values.tolist()
    lstZ = dfbars[lstSymbol].loc[index.tolist()[-2]].values.tolist()
    lstU = dfbars[lstSymbol].loc[index.tolist()[-7]].values.tolist()
    lstW = dfbars[lstSymbol].loc[index.tolist()[-20]].values.tolist()
    p1 = plotLineGraphItem(productid+U"-价格",lstX,lstY,lstZ,lstU,lstW)

    lstY = dfstd[lstSymbol].loc[index.tolist()[-1]].values.tolist()
    lstZ = dfstd[lstSymbol].loc[index.tolist()[-2]].values.tolist()
    lstU = dfstd[lstSymbol].loc[index.tolist()[-7]].values.tolist()
    lstW = dfstd[lstSymbol].loc[index.tolist()[-20]].values.tolist()
    p2 = plotLineGraphItem(productid+U"-波动率",lstX,lstY,lstZ,lstU,lstW)
    return p1,p2

def getSpread(symbol1,symbol2):
    bar1 = db.getBarsbyDay(symbol1)[['tradingday','closeprice']]
    bar2 = db.getBarsbyDay(symbol2)[['tradingday','closeprice']]
    dfbars = pd.merge(bar1,bar2,on='tradingday',how='inner')
    dfbars['spread'] = dfbars['closeprice_x'] - dfbars['closeprice_y']
    return dfbars[['tradingday','spread']]

class Communicate(QObject):
    emitButton = pyqtSignal(float)

class uiStructuretool(QtGui.QWidget,object):
    Signal = QtCore.pyqtSignal()
    #----------------------------------------------------------------------
    def __init__(self,eventEngine,parent=None):
        """Constructor"""
        self.parent = parent
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle(u'期限监控')
        self.setWindowIcon(QtGui.QIcon('./icons/stock.ico'))

        self.eventEngine = eventEngine
        self.eventEngine.start()
        self.eventEngine.register("showData",self.showData)
        self.eventEngine.register("showSpread",self.showSpread)
        self.eventEngine.register("showSelect",self.showSelect)

        self.view = pg.GraphicsView()
        self.view.resize(800,600)
        self.l = pg.GraphicsLayout(border=(100,100,100))
        self.l.resize(800,600)
        self.view.setCentralItem(self.l)
        self.view.show()

        #期现结构按钮
        self.btn_load = QtWidgets.QPushButton(U'期现结构',self)
        self.btn_load.setGeometry(QtCore.QRect(242, 0, 81, 25))
        self.btn_load.setFixedSize(80,35)
        self.btn_load.setObjectName("btn_load")
        self.btn_load.clicked.connect(self.clickedbutton)

        self.c = Communicate()
        self.c.emitButton.connect(self.emitSignal)
        self.c1 = Communicate()
        self.c1.emitButton.connect(self.emitSpred)
        self.c2 = Communicate()
        self.c2.emitButton.connect(self.emitSelect)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label.setFixedSize(50,35)
        self.label.setObjectName("label")
        self.label.setText(U"品种")

        self.cbb_model = QtWidgets.QComboBox(self)
        self.cbb_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.cbb_model.setFixedSize(80,35)
        self.cbb_model.setObjectName("cbb_model")
        self.cbb_model.addItem("AP")
        self.cbb_model.addItem("CF")
        self.cbb_model.addItem("ZC")
        self.cbb_model.addItem("TA")
        self.cbb_model.addItem("b")
        self.cbb_model.addItem("c")
        self.cbb_model.addItem("m")
        self.cbb_model.addItem("jd")
        self.cbb_model.addItem("i")
        self.cbb_model.addItem("ni")
        self.cbb_model.addItem("sc")
        self.cbb_model.addItem("SR")
        self.cbb_model.addItem("pp")
        self.cbb_model.addItem("l")
        self.cbb_model.addItem("MA")
        self.cbb_model.addItem("jm")
        self.cbb_model.addItem("cu")
        self.cbb_model.addItem("al")
        self.cbb_model.addItem("zn")
        self.cbb_model.addItem("pb")
        self.cbb_model.addItem("sn")
        self.cbb_model.addItem("au")
        self.cbb_model.addItem("ag")
        self.cbb_model.addItem("ru")
        self.cbb_model.addItem("rb")
        self.cbb_model.addItem("hc")
        self.cbb_model.addItem("bu")
        self.cbb_model.addItem("y")
        self.cbb_model.addItem("a")
        self.cbb_model.addItem("p")
        self.cbb_model.addItem("cs")
        self.cbb_model.addItem("v")
        self.cbb_model.addItem("j")
        self.cbb_model.addItem("FG")
        self.cbb_model.addItem("OI")
        self.cbb_model.addItem("RM")
        self.cbb_model.addItem("SF")
        self.cbb_model.addItem("SM")
        self.cbb_model.addItem("CY")
        self.cbb_model.addItem("IF")
        self.cbb_model.addItem("IH")
        self.cbb_model.addItem("IC")
        self.cbb_model.addItem("T")
        self.cbb_model.addItem("TF")
        self.cbb_model.setCurrentIndex(0)

        # 设置界面
        self.hb1 = QtGui.QVBoxLayout()
        self.hb1.setContentsMargins(15, 0, 15, 0)
        self.hb1.addWidget(self.view)

        self.hb2 = QtGui.QGridLayout()
        self.wd = StructWidget()
        self.hb2.addWidget(self.wd,0,0)
        self.black = QtGui.QWidget()

        self.hb2.addWidget(self.wd,0,1)
        self.hb2.addWidget(self.wd,0,0)

        self.hb = QtGui.QVBoxLayout()
        self.hb.addLayout(self.hb1)
        self.hb.addLayout(self.hb2)

        self.mainb = QtGui.QHBoxLayout()
        self.mainb.addLayout(self.hb)

        self.lastb = QtGui.QVBoxLayout()

        self.vb3 = QtGui.QHBoxLayout()
        self.vb3.addWidget(self.label)
        self.vb3.addWidget(self.cbb_model)
        self.vb3.addWidget(self.btn_load)

        self.vb3.addWidget(QtWidgets.QLabel(self))

        self.vbselect = QtGui.QFormLayout()
        self.mainb.addLayout(self.vbselect)

        self.lastb.addLayout(self.vb3)
        self.lastb.addLayout(self.mainb)
        self.setLayout(self.lastb)
        self.counts = 0

    def clickedbutton(self):
        event = Event("showData")
        self.eventEngine.put(event)

    def clickedspreadbutton(self):
        event = Event("showSpread")
        self.eventEngine.put(event)

    def clickedselect(self):
        event = Event("showSelect")
        self.eventEngine.put(event)

    def emitSpred(self,p):
        self.wd = StructWidget()
        self.hb2.addWidget(self.wd,0,0)
        self.wd.loadData(self.spreaddata,self.spreadtitle)

    def emitSelect(self,p):
        sym = []
        for i in range(0,len(self.checkBox)):
            if self.checkBox[i].checkState() == 2:
                sym.append(self.symbols[i])
        self.p1.clear()
        self.p2.clear()
        self.p1,self.p2 = getDatabySymbol(sym,self.productid)

        self.l.clear()
        self.l.nextRow()
        self.l.addItem(self.p1)
        self.l.addItem(self.p2)
        self.l.nextRow()

    def emitSignal(self,p):
        if self.counts > 0:
            sip.delete(self.btn_load1)
            sip.delete(self.btn_load2)
            for cb in self.checkBox:
                sip.delete(cb)
        self.counts = self.counts + 1
        self.p1,self.p2 = getDatas(self.productid,self.sday)
        self.l.clear()
        self.l.nextRow()
        self.l.addItem(self.p1)
        self.l.addItem(self.p2)
        self.setLayout(self.lastb)

        symbol = db.getTradeSymbol_productid(self.productid,self.sday)
        self.symbols = symbol['symbol'].values.tolist()
        self.checkBox = []
        for sym in self.symbols:
            ck = QtWidgets.QCheckBox(sym)
            ck.setFocusPolicy(QtCore.Qt.NoFocus)
            #ck.move(10, 10)
            ck.setChecked(True)
            ck.setMinimumWidth(80)
            ck.toggle()
            self.checkBox.append(ck)
            self.vbselect.addWidget(ck)

        self.btn_load1 = QtWidgets.QPushButton(U'价差分析',self)
        self.btn_load1.setGeometry(QtCore.QRect(242, 0, 81, 25))
        self.btn_load1.setFixedSize(80,35)
        self.btn_load1.setObjectName("btn_analysis")
        self.btn_load1.clicked.connect(self.clickedspreadbutton)
        self.vbselect.addWidget(self.btn_load1)
        #过滤
        self.btn_load2 = QtWidgets.QPushButton(U'选择合约',self)
        self.btn_load2.setGeometry(QtCore.QRect(242, 0, 81, 25))
        self.btn_load2.setFixedSize(80,35)
        self.btn_load2.setObjectName("btn_select")
        self.btn_load2.clicked.connect(self.clickedselect)
        self.vbselect.addWidget(self.btn_load2)

    def showData(self,event):
        self.productid = self.cbb_model.currentText()
        self.sday = db.getLstTradingDay()
        self.c.emitButton.emit(0.1)

    def showSpread(self,event):
        sym = []
        for i in range(0,len(self.checkBox)):
            if self.checkBox[i].checkState() == 2:
                sym.append(self.symbols[i])
        if len(sym) < 2:
            return
        self.spreaddata = getSpread(sym[0],sym[1])
        self.spreadtitle = U'价差'+"("+sym[0]+"-"+sym[1]+")"
        self.p3 = plotLineSpreadItem(U'价差'+"("+sym[0]+"-"+sym[1]+")",self.spreaddata)
        self.c1.emitButton.emit(0.1)

    def showSelect(self,event):
        self.c2.emitButton.emit(0.1)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # 期限结构界面
    ee = EventEngine()
    ui = uiStructuretool(ee)
    ui.showMaximized()
    app.exec_()
