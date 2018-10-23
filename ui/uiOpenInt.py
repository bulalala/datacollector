# -*- coding: utf-8 -*-

from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtCore import pyqtSignal,QObject
import pyqtgraph as pg
from VaR import *
import re
from eventEngine import *

db = dbWrapper('postgres-a1mzuj9c.sql.tencentcdb.com')

def getIndustry(productID):
    if productID in ['rb', 'j','jm','i','hc','ZC','FG','SM','SF']:
        return U"黑色"
    elif productID in ['pp', 'l', 'MA', 'bu', 'TA', 'v','sc','ru','fu']:
        return U"能源化工"
    elif productID in ['cu', 'al', 'zn', 'pb', 'ni', 'sn']:
        return U"有色"
    elif productID in [ 'c', 'cs', 'jd','WH','PM']:
        return U"谷物"
    elif productID in ['y', 'p', 'OI','m','RM','a','b']:
        return U"豆系"
    elif productID in ['ag','au']:
        return U"贵金属"
    elif productID in ['CF','SR','CY','AP']:
        return U"软商品"
    elif productID in ['T','TF']:
        return U"国债"
    elif productID in ['IF','IC','IH']:
        return U"股指"
    else:
        return U"其他"

class Communicate(QObject):
    closeApp = pyqtSignal(float)


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.RectMode)

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.autoRange()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)


class TestWidget(QtGui.QWidget,object):
    Signal = QtCore.pyqtSignal()
    #----------------------------------------------------------------------
    def __init__(self,eventEngine,parent=None):
        """Constructor"""
        self.parent = parent
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle(u'持仓分析')
        self.setWindowIcon(QtGui.QIcon('./icons/stock.ico'))

        self.eventEngine = eventEngine
        self.eventEngine.start()
        self.eventEngine.register("showData",self.showData)

        self.view = pg.GraphicsView()
        self.l = pg.GraphicsLayout(border=(100,100,100))
        self.view.setCentralItem(self.l)
        self.view.show()
        self.view.resize(800,600)

        self.view2 = pg.GraphicsView()
        self.l2 = pg.GraphicsLayout(border=(100,100,100))
        self.view2.setCentralItem(self.l2)
        self.view2.show()
        self.view2.resize(800,600)

        self.x = []
        self.y = []
        self.x1 = []
        self.y1 = []
        self.x2 = []
        self.y2 = []
        self.x_contract = []
        self.y_contract = []

        self.lstBlack = ['rb', 'j','jm','i','hc','ZC','FG','SM','SF']
        self.lstChemical = ['pp', 'l', 'MA', 'bu', 'TA', 'v','fu', 'sc', 'ru']
        self.lstMetal = [ 'cu', 'al','zn', 'pb', 'ni', 'sn']
        self.lstGoal = ['ag','au']
        self.lstGrain = ['c', 'cs', 'jd','WH','PM']
        self.lstBeen = ['y', 'p', 'OI','m','RM','a','b']
        self.lstSoft = ['CF','SR','CY','AP']
        self.lstFinance = ['IF','IC','IH','T','TF']

        self.btn_load = QtWidgets.QPushButton(U'分析',self)
        self.btn_load.setGeometry(QtCore.QRect(242, 0, 81, 25))
        self.btn_load.setFixedSize(80,35)
        self.btn_load.setObjectName("btn_load")
        self.btn_load.clicked.connect(self.clickedbutton)

        self.c = Communicate()
        self.c.closeApp.connect(self.emitSignal)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label.setFixedSize(40,35)
        self.label.setObjectName("label")
        self.label.setText(U"席位")

        self.label1 = QtWidgets.QLabel(self)
        self.label1.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label1.setFixedSize(40,35)
        self.label1.setObjectName("label")
        self.label1.setText(U"日期")

        self.cbb_model = QtWidgets.QComboBox(self)
        self.cbb_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.cbb_model.setFixedSize(180,35)
        self.cbb_model.setObjectName("cbb_model")

        self.date_model = QtWidgets.QComboBox(self)
        self.date_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.date_model.setFixedSize(120,35)
        self.date_model.setObjectName("date_model")

        self.tradingdays = db.getOpenIntTradingDay()

        self.initCompany()
        self.cbb_model.setCurrentIndex(0)
        self.date_model.setCurrentIndex(0)

        self.initUI()
        # 设置界面
        self.hb = QtGui.QVBoxLayout()
        #self.hb.addWidget(self.btn_load)
        self.hb.addWidget(self.view)
        self.hb.addWidget(self.view2)
        self.mainb = QtGui.QHBoxLayout()
        self.mainb.addLayout(self.hb)

        self.lastb = QtGui.QVBoxLayout()

        self.vb3 = QtGui.QHBoxLayout()
        self.vb3.addWidget(self.label)
        self.vb3.addWidget(self.cbb_model)
        self.vb3.addWidget(self.label1)
        self.vb3.addWidget(self.date_model)
        self.vb3.addWidget(self.btn_load)
        self.vb3.addWidget(QtWidgets.QLabel(self))

        self.lastb.addLayout(self.vb3)
        self.lastb.addLayout(self.mainb)
        self.setLayout(self.lastb)

    def initCompany(self):
        # self.cbb_model.addItem("上海中期")
        # self.cbb_model.addItem("海通期货")
        # self.cbb_model.addItem("华泰期货")
        # self.cbb_model.addItem("永安期货")
        # self.cbb_model.addItem("申%万")
        # self.cbb_model.addItem("国泰君安")
        # self.cbb_model.addItem("南华期货")
        # self.cbb_model.addItem("新湖期货")
        # self.cbb_model.addItem("浙商期货")
        # self.cbb_model.addItem("中信建投")
        # self.cbb_model.addItem("中信期货")
        # self.cbb_model.addItem("光大期货")
        # self.cbb_model.addItem("中粮期货")
        # self.cbb_model.addItem("广发期货")
        # self.cbb_model.addItem("格林大华")
        # self.cbb_model.addItem("国投安信")
        # self.cbb_model.addItem("金瑞期货")
        # self.cbb_model.addItem("一德期货")
        # self.cbb_model.addItem("银河期货")
        # self.cbb_model.addItem("兴证期货")
        # self.cbb_model.addItem("兴业期货")
        # self.cbb_model.addItem("中证期货")
        # self.cbb_model.addItem("中国国际")
        # self.cbb_model.addItem("摩根大通")
        # self.cbb_model.addItem("五矿经易")
        # self.cbb_model.addItem("混沌天成")
        # self.cbb_model.addItem("华信期货")
        # self.cbb_model.addItem("国联期货")
        # self.cbb_model.addItem("渤海期货")
        # self.cbb_model.addItem("东航期货")
        # self.cbb_model.addItem("鲁证期货")
        companies = db.getAllCompany()
        for com in companies:
            self.cbb_model.addItem(com)
        for i in range(len(self.tradingdays)-1,1,-1):
            self.date_model.addItem(self.tradingdays.loc[i,'tradingday'])

    def plotBarGraphItem(self,name,lstX=[],lstY=[]):
        if len(lstX)==0:
            return pg.PlotItem(title=name)
        ticklist = []
        ix = []
        i = 0
        p = pg.PlotItem(title=name)
        for x in lstX:
            ticklist.append((i, x))
            ix.append(i)
            if lstY[i] > 0:
                k = 0.5
            else:
                k = 0
            #text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">'+ "%.1f"%(lstY[i]) + '</span><br></div>', anchor=(0.5,k), angle=0)
            #p.addItem(text)
            #text.setPos(i,lstY[i])
            i = i+1
        for i in ix:
            if lstY[i] >= 0:
                scolor = 'r'
            else:
                scolor = 'g'
            bg1 = pg.BarGraphItem(x=[ix[i]], height=[lstY[i]], width=0.3, brush=scolor)
            p.addItem(bg1)
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p

    def plotDoubleBarGraphItem(self,name,lstX=[],lstY=[],lstY2=[]):
        if len(lstX)==0:
            return pg.PlotItem(title=name)
        ticklist = []
        ix = []
        ix2 = []
        i = 0
        p = pg.PlotItem(title=name)
        for x in lstX:
            ticklist.append((i+0.15, x))
            ix.append(i)
            ix2.append(i+0.33)
            i = i+1
        bg1 = pg.BarGraphItem(x=ix, height=lstY, width=0.3, brush='r')
        p.addItem(bg1)
        bg2 = pg.BarGraphItem(x=ix2, height=lstY2, width=0.3, brush='b')
        p.addItem(bg2)
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p

    def plotLineGraphItem(self,name,lstX=[],lstY=[]):
        p = pg.PlotItem(title=name)
        if len(lstX)==0:
            return p
        i = 0
        ticklist = []
        for x in lstX:
            ticklist.append((x, "%.2f"%(x)))
            if lstY[i] > 0:
                k = 0.5
            else:
                k = 0
            text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">'+ "%.1f"%(lstY[i]) + '</span><br></div>', anchor=(0.5,k), angle=0)
            p.addItem(text)
            text.setPos(x,lstY[i])
            i = i + 1
        p.plot(lstX, lstY, symbol='o',symbolBrush=(255,0,0))
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p



    def initUI(self):
        self.p1 = self.plotBarGraphItem(U'净头寸',self.x,self.y)
        self.l.nextRow()
        self.l.addItem(self.p1)
        self.p2 = self.plotBarGraphItem(U'总体持仓分布',self.x1,self.y1)
        self.l.addItem(self.p2)
        self.l2.nextRow()
        p = self.plotBarGraphItem(U'各合约持仓分布',self.x_contract,self.y_contract)
        self.l2.addItem(p)


    def clearData(self):
        self.x = []
        self.y = []
        self.x1 = []
        self.y1 = []
        self.x2 = []
        self.y2 = []

    def showData(self,event):
        self.clearData()
        days = self.date_model.currentText()
        tradingay = self.tradingdays[self.tradingdays.tradingday <= days]
        self.company = self.cbb_model.currentText()
        self.company = (re.sub(U'[期货]', '', self.company))
        if self.company == U'申万' or self.company == U'申银万国':
            self.company = U'%申%万'
        self.today = tradingay['tradingday'].loc[tradingay.index.values[-1]]
        self.yestoday = tradingay['tradingday'].loc[tradingay.index.values[-2]]
        settlementprice_cur = db.getAllSettlementPrice(self.today)
        openint_cur = db.getDataBySeat(self.company,self.today)
        if len(openint_cur) == 0:
            return
        df_cur = pd.merge(openint_cur,settlementprice_cur,on=['symbol'],how='left')
        df_cur['marketvalue'] = df_cur['quatity']*df_cur['settlementprice']*df_cur['multipler']/10000
        grouped_cur = df_cur['marketvalue'].groupby(df_cur['productid']).sum()
        df_cur = df_cur.sort_values(by = 'symbol',axis = 0,ascending = True)
        df_cur.index = range(0,len(df_cur))
        self.x_contract = df_cur['symbol'].tolist()
        self.y_contract = df_cur['marketvalue'].values.tolist()
        self.dicIndustry_cur = {}
        self.dicBlack = {}
        self.dicChemitry = {}
        self.dicMetal = {}
        self.dicGoal = {}
        self.dicBean = {}
        self.dicSoft = {}
        self.dicGrain = {}
        self.dicFinance = {}
        #for productid in grouped_cur.index:
        for productid in self.lstBlack:
            if productid in grouped_cur:
                self.dicBlack[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        for productid in self.lstChemical:
            if productid in grouped_cur:
                self.dicChemitry[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #有色
        for productid in self.lstMetal:
            if productid in grouped_cur:
                self.dicMetal[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #贵金属
        for productid in self.lstGoal:
            if productid in grouped_cur:
                self.dicGoal[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #豆系
        for productid in self.lstBeen:
            if productid in grouped_cur:
                self.dicBean[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #软商品
        for productid in self.lstSoft:
            if productid in grouped_cur:
                self.dicSoft[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #谷物
        for productid in self.lstGrain:
            if productid in grouped_cur:
                self.dicGrain[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        #金融
        for productid in self.lstFinance:
            if productid in grouped_cur:
                self.dicFinance[productid] = grouped_cur[productid]
                sIndustry = getIndustry(productid)
                if sIndustry in self.dicIndustry_cur:
                    self.dicIndustry_cur[sIndustry] = self.dicIndustry_cur[sIndustry] + grouped_cur[productid]
                else:
                    self.dicIndustry_cur[sIndustry] = grouped_cur[productid]

        sortindustry_cur = sorted(self.dicIndustry_cur.items(),key=lambda d:d[1], reverse = True)
        sortBlack = sorted(self.dicBlack.items(),key=lambda d:d[1], reverse = True)
        sortChemitry = sorted(self.dicChemitry.items(),key=lambda d:d[1], reverse = True)
        sortMetral = sorted(self.dicMetal.items(),key=lambda d:d[1], reverse = True)
        sortGoal = sorted(self.dicGoal.items(),key=lambda d:d[1], reverse = True)
        sortBean = sorted(self.dicBean.items(),key=lambda d:d[1], reverse = True)
        sortSoft = sorted(self.dicSoft.items(),key=lambda d:d[1], reverse = True)
        sortGrain = sorted(self.dicGrain.items(),key=lambda d:d[1], reverse = True)
        sortFinance = sorted(self.dicFinance.items(),key=lambda d:d[1], reverse = True)
        #上一交易日
        settlementprice = db.getAllSettlementPrice(self.yestoday)
        openint = db.getDataBySeat(self.company,self.yestoday)
        df = pd.merge(openint,settlementprice,on=['symbol'],how='left')
        df['marketvalue'] = df['quatity']*df['settlementprice']*df['multipler']/10000
        grouped = df['marketvalue'].groupby(df['productid']).sum()
        self.dicIndustry = {}
        for productid in grouped.index:
            sIndustry = getIndustry(productid)
            if sIndustry in self.dicIndustry:
                self.dicIndustry[sIndustry] = self.dicIndustry[sIndustry] + grouped[productid]
            else:
                self.dicIndustry[sIndustry] = grouped[productid]
        for i in sortBlack:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortChemitry:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortMetral:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortGoal:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortBean:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortSoft:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortGrain:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortFinance:
            self.x.append(i[0])
            self.y.append(i[1])
        for i in sortindustry_cur:
            self.x1.append(i[0])
            self.y1.append(i[1])
            self.x2.append(i[0])
            if i[0] in self.dicIndustry:
                self.y2.append(i[1] - self.dicIndustry[i[0]])
            else:
                 self.y2.append(i[1])
        self.c.closeApp.emit(0.95)

    def clickedbutton(self):
        #self.eventEngine.register(EVENT_TIMER,self.pintdatas)
        event = Event("showData")
        self.eventEngine.put(event)

    def emitSignal(self,alpha):
        self.l.clear()
        self.l.nextRow()
        stitle = self.company + U'净头寸' + '(' + self.today + ')'
        self.p1 = self.plotBarGraphItem(stitle,self.x,self.y)    #净头寸分布
        self.l.addItem(self.p1)
        stitle = self.company + U'总体持仓分布' + '(' + self.today + ')'
        self.p2 = self.plotDoubleBarGraphItem(stitle,self.x1,self.y1,self.y2)
        self.l.addItem(self.p2)

        self.l2.clear()
        self.l2.nextRow()
        stitle = self.company + U'各合约持仓分布' + '(' + self.today + ')'
        p = self.plotBarGraphItem(stitle,self.x_contract,self.y_contract)
        self.l2.addItem(p)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    # 界面设置
    ee = EventEngine()
    ui = TestWidget(ee)
    ui.showMaximized()
    app.exec_()
