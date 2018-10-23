# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtCore import pyqtSignal,QObject
import pyqtgraph as pg
from VaR import *
import re
from eventEngine import *

db = dbWrapper('postgres-a1mzuj9c.sql.tencentcdb.com')
#db.create_openint_index_table()

def update_maketvalue(stradingday):
    dfopenint = db.getDataByTradingday(stradingday)
    settlementprice = db.getAllSettlementPrice(stradingday)
    df_cur = pd.merge(dfopenint,settlementprice,on=['symbol'],how='left')
    df_cur['marketvalue'] = df_cur['quatity']*df_cur['settlementprice']*df_cur['multipler']/10000
    df = df_cur[['company','productid','symbol','marketvalue']]
    #print(df_cur)
    for (k1,k2),group in  df_cur[['company','productid','marketvalue']].groupby(['company','productid']):
        dftmp = pd.DataFrame([k1,k2,'all',group['marketvalue'].sum()])
        dftmp = dftmp.T
        dftmp.columns = ['company','productid','symbol','marketvalue']
        df = df.append(dftmp)
    df.index = range(0,len(df))
    df['tradingday'] = stradingday
    return df


# tradingday = db.getOpenIntTradingDay()
# for day in tradingday['tradingday'].values.tolist():
#     print day
#     data = update_maketvalue(day)
#     db.batchup_openint_index(data)
#print db.get_marketvalue_byproductid('i',U'永安期货')

class Communicate(QObject):
    closeApp = pyqtSignal(float)

def plotLineGraphItem(name,lstX=[],lstY=[]):
        p = pg.PlotItem(title=name)
        if len(lstX)==0:
            return p
        i = 0
        ticklist = []
        # for x in lstX:
        #     ticklist.append((x, "%.2f"%(x)))
        #     if lstY[i] > 0:
        #         k = 0.5
        #     else:
        #         k = 0
        #     text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">'+ "%.1f"%(lstY[i]) + '</span><br></div>', anchor=(0.5,k), angle=0)
        #     p.addItem(text)
        #     text.setPos(x,lstY[i])
        #     i = i + 1
        for i in range(0,len(lstX)):
            if i%5 == 0:
                ticklist.append((i, lstX[i]))

        lstX = range(0,len(lstY))
        p.plot(lstX, lstY, symbol='o',symbolBrush=(255,0,0))
        p.getAxis("bottom").setTicks([ticklist,[]])
        return p

class StatisticWidget(QtGui.QWidget,object):
    Signal = QtCore.pyqtSignal()
    #----------------------------------------------------------------------
    def __init__(self,eventEngine,parent=None):
        """Constructor"""
        self.parent = parent
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle(u'历史统计')
        self.setWindowIcon(QtGui.QIcon('./icons/stock.ico'))

        self.eventEngine = eventEngine
        self.eventEngine.start()
        #self.eventEngine.register("showData",self.showData)

        self.view = pg.GraphicsView()
        self.l = pg.GraphicsLayout(border=(100,100,100))
        self.view.setCentralItem(self.l)
        self.view.show()
        self.view.resize(800,600)

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

        self.label2 = QtWidgets.QLabel(self)
        self.label2.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label2.setFixedSize(40,35)
        self.label2.setObjectName("label")
        self.label2.setText(U"排名")

        self.cbb_model = QtWidgets.QComboBox(self)
        self.cbb_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.cbb_model.setFixedSize(180,35)
        self.cbb_model.setObjectName("cbb_model")

        self.productid_model = QtWidgets.QComboBox(self)
        self.productid_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.productid_model.setFixedSize(120,35)
        self.productid_model.setObjectName("date_model")

        self.rank_model = QtWidgets.QComboBox(self)
        self.rank_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.rank_model.setFixedSize(120,35)
        self.rank_model.setObjectName("rank_model")

        self.tradingdays = db.getOpenIntTradingDay()

        self.initCompany()
        self.cbb_model.setCurrentIndex(0)
        self.productid_model.setCurrentIndex(0)

        self.initUI()
        # 设置界面
        self.hb = QtGui.QVBoxLayout()
        #self.hb.addWidget(self.btn_load)
        self.hb.addWidget(self.view)
        self.mainb = QtGui.QHBoxLayout()
        self.mainb.addLayout(self.hb)

        self.lastb = QtGui.QVBoxLayout()

        self.vb3 = QtGui.QHBoxLayout()
        self.vb3.addWidget(self.label)
        self.vb3.addWidget(self.cbb_model)
        self.vb3.addWidget(self.label1)
        self.vb3.addWidget(self.productid_model)
        self.vb3.addWidget(self.label2)
        self.vb3.addWidget(self.rank_model)
        self.vb3.addWidget(self.btn_load)

        self.vb3.addWidget(QtWidgets.QLabel(self))

        self.lastb.addLayout(self.vb3)
        self.lastb.addLayout(self.mainb)
        self.setLayout(self.lastb)

    def clickedbutton(self):
        productid = self.productid_model.currentText()
        company = self.cbb_model.currentText()
        company = (re.sub(U'[期货]', '', company))
        if company == U'申万' or company == U'申银万国':
            company = U'%申%万'
        irank = self.rank_model.currentText()
        data = db.get_marketvalue_byproductid(productid,company)
        self.l.clear()
        if len(data) != 0:
            title = company+productid+U"持仓市值变化"
            pp = plotLineGraphItem(title,data['tradingday'].values.tolist(),data['marketvalue'].values.tolist())
            self.l.nextRow()
            self.l.addItem(pp)

        data = db.get_marketvalue_by_longrank(productid,irank)
        long_grouped = data.groupby(['tradingday']).sum()
        long_grouped['tradingday'] = long_grouped.index
        long_grouped.index = range(0,len(long_grouped))
        title = productid+U"前"+irank+U"名持多仓市值变化"
        pp2 = plotLineGraphItem(title,long_grouped['tradingday'].values.tolist(),long_grouped['marketvalue'].values.tolist())

        data = db.get_marketvalue_by_shortrank(productid,irank)
        short_grouped = data.groupby(['tradingday']).sum()
        short_grouped['tradingday'] = short_grouped.index
        short_grouped.index = range(0,len(short_grouped))
        title = productid+U"前"+irank+U"名持空仓市值变化"
        pp3 = plotLineGraphItem(title,short_grouped['tradingday'].values.tolist(),short_grouped['marketvalue'].values.tolist())

        net = long_grouped.merge(short_grouped,on=['tradingday'])
        net['marketvalue'] = net['marketvalue_x'] + net['marketvalue_y']
        title = productid+U"前"+irank+U"名净持仓市值变化"
        pp4 = plotLineGraphItem(title,net['tradingday'].values.tolist(),net['marketvalue'].values.tolist())
        print(net)

        self.l.nextRow()
        self.l.addItem(pp4)
        self.l.nextRow()
        self.l.addItem(pp2)
        self.l.nextRow()
        self.l.addItem(pp3)



    def emitSignal(self,alpha):
        return

    def initUI(self):
        return


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

        self.productid_model.addItem("cu")
        self.productid_model.addItem("al")
        self.productid_model.addItem("zn")
        self.productid_model.addItem("pb")
        self.productid_model.addItem("ni")
        self.productid_model.addItem("sn")
        self.productid_model.addItem("au")
        self.productid_model.addItem("ag")
        self.productid_model.addItem("rb")
        self.productid_model.addItem("hc")
        self.productid_model.addItem("fu")
        self.productid_model.addItem("bu")
        self.productid_model.addItem("sc")
        self.productid_model.addItem("ru")
        self.productid_model.addItem("m")
        self.productid_model.addItem("y")
        self.productid_model.addItem("a")
        self.productid_model.addItem("b")
        self.productid_model.addItem("p")
        self.productid_model.addItem("c")
        self.productid_model.addItem("cs")
        self.productid_model.addItem("jd")
        self.productid_model.addItem("l")
        self.productid_model.addItem("v")
        self.productid_model.addItem("pp")
        self.productid_model.addItem("j")
        self.productid_model.addItem("jm")
        self.productid_model.addItem("i")
        self.productid_model.addItem("SR")
        self.productid_model.addItem("CF")
        self.productid_model.addItem("ZC")
        self.productid_model.addItem("FG")
        self.productid_model.addItem("TA")
        self.productid_model.addItem("MA")
        self.productid_model.addItem("WH")
        self.productid_model.addItem("OI")
        self.productid_model.addItem("SF")
        self.productid_model.addItem("SM")
        self.productid_model.addItem("CY")
        self.productid_model.addItem("AP")

        self.rank_model.addItem('5')
        self.rank_model.addItem('10')
        self.rank_model.addItem('20')

def insert_index(stradingday):
    df = update_maketvalue(stradingday)
    if len(df)==0:
        return
    df = df.sort_values(by='marketvalue',ascending = False)
    print(df)
    for (k1,k2),group in  df.groupby(['productid','symbol']):
        data = group
        data['long_rank'] = range(1,len(data)+1)
        data['short_rank'] = range(len(data),0,-1)
        data.index = range(0,len(data))
        db.batchup_openint_index2(data)
        print(data)

#db.create_openint_index_table()
# tradingday = db.getOpenIntTradingDay()
# for day in tradingday['tradingday'].values.tolist():
#     insert_index(day)
#     print day

data = db.get_marketvalue_by_shortrank('rb',5)
grouped = data.groupby(['tradingday']).sum()
grouped['tradingday'] = grouped.index
grouped.index = range(0,len(grouped))
print(grouped)

# import sys
# app = QtGui.QApplication(sys.argv)
# # 界面设置
# ee = EventEngine()
# ui = StatisticWidget(ee)
# ui.showMaximized()
# app.exec_()

