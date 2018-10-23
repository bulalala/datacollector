# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtCore import pyqtSignal,QObject
import pyqtgraph as pg
from VaR import *
import re
from eventEngine import *

db = dbWrapper('postgres-fj7nqbmu.sql.tencentcdb.com')

def getIndustry(productID):
    if productID in ['rb', 'j','jm','i','hc','ZC','FG','SM','SF']:
        return U"黑色"
    elif productID in ['pp', 'l', 'MA', 'bu', 'TA', 'v','sc','fu']:
        return U"化工"
    elif productID in ['cu', 'al', 'zn', 'pb', 'ni', 'sn']:
        return U"有色"
    elif productID in [ 'c', 'cs', 'jd','WH','PM']:
        return U"谷物"
    elif productID in ['y', 'p', 'OI','m','RM','a','b']:
        return U"豆系"
    elif productID in ['ru']:
        return U"橡胶"
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
        self.setWindowTitle(u'VaR监控')
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

        self.btn_load = QtWidgets.QPushButton(U'计算',self)
        self.btn_load.setGeometry(QtCore.QRect(242, 0, 81, 25))
        #font = QtGui.QFont()
        #font.setPointSize(12)
        #font.setBold(True)
        #font.setWeight(75)
        self.btn_load.setFixedSize(80,35)
        #self.btn_load.setFont(font)
        self.btn_load.setObjectName("btn_load")
        self.btn_load.clicked.connect(self.clickedbutton)


        self.c = Communicate()
        self.c.closeApp.connect(self.emitSignal)



        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(0, 0, 31, 25))
        self.label.setFixedSize(80,35)
        self.label.setObjectName("label")
        self.label.setText(U"置信区间")

        self.cbb_model = QtWidgets.QComboBox(self)
        self.cbb_model.setGeometry(QtCore.QRect(500, 0, 51, 25))
        self.cbb_model.setFixedSize(80,35)
        self.cbb_model.setObjectName("cbb_model")
        self.cbb_model.addItem("0.95")
        self.cbb_model.addItem("0.97")
        self.cbb_model.addItem("0.99")
        self.cbb_model.setCurrentIndex(0)

        self.initUI()
        # 设置界面
        self.hb = QtGui.QVBoxLayout()
        #self.hb.addWidget(self.btn_load)
        self.hb.addWidget(self.view)
        self.mainb = QtGui.QHBoxLayout()
        self.mainb.addLayout(self.hb)
        self.vb2 = QtGui.QVBoxLayout()
        self.vb2.addWidget(self.view2)
        self.mainb.addLayout(self.vb2)
        self.lastb = QtGui.QVBoxLayout()

        self.vb3 = QtGui.QHBoxLayout()
        self.vb3.addWidget(self.label)
        self.vb3.addWidget(self.cbb_model)
        self.vb3.addWidget(self.btn_load)
        self.vb3.addWidget(QtWidgets.QLabel(self))

        self.lastb.addLayout(self.vb3)
        self.lastb.addLayout(self.mainb)
        self.view2.setFixedWidth(600)
        self.setLayout(self.lastb)

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
            text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">'+ "%.1f"%(lstY[i]) + '</span><br></div>', anchor=(0.5,k), angle=0)
            p.addItem(text)
            text.setPos(i,lstY[i])

            i = i+1
        bg1 = pg.BarGraphItem(x=ix, height=lstY, width=0.3, brush='r')
        p.addItem(bg1)
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
        self.p1 = self.plotBarGraphItem('VaR-0.95',self.x,self.y)
        self.l.nextRow()
        self.l.addItem(self.p1)
        self.l.nextRow()
        self.p2 = self.plotBarGraphItem(U'持仓市值',self.x1,self.y1)
        self.l.addItem(self.p2)

        self.p3 = self.plotLineGraphItem(U'组合VaR',self.x,self.y)
        self.l2.nextRow()
        self.l2.addItem(self.p3)
        self.l2.nextRow()
        self.p4 = self.plotBarGraphItem(U'总持仓市值',self.x1,self.y1)
        self.l2.addItem(self.p4)
        self.l2.nextRow()
        self.p5 = self.plotBarGraphItem(U'行业分布',self.x1,self.y1)
        self.l2.addItem(self.p5)




    def clearData(self):
        self.x = []
        self.y = []
        self.x1 = []
        self.y1 = []

    def showData(self,event):
        self.clearData()
        alpha1 = 0.95
        if self.cbb_model.currentIndex() == 0:
            alpha1 = 0.95
        elif self.cbb_model.currentIndex() == 1:
            alpha1 = 0.97
        elif self.cbb_model.currentIndex() == 2:
            alpha1 = 0.99
        sday = db.getLstTradingDay()
        lstsymbol,lstpos = readCSV()
        capital,diccapital = getCaptital(lstsymbol,lstpos,sday)
        dfdata = calPortfolioReturn(diccapital,capital,alpha1)
        data = VaR_sim(dfdata,alpha1)
        self.x3 = ['total']
        self.x4 = ['total','net']

        self.dicIndustry = {}
        self.x5 = []  #行业数据
        self.y5 = []
        #VaR分布
        self.x6 = [0.91,0.93,0.95,0.97,0.99]
        self.y6 = []

        dicValue = {}
        for key in diccapital:
            dicValue[key] = abs(diccapital[key])*dicVaR[key]
            sIndustry = getIndustry(re.findall(r'[a-zA-Z]+', key)[0])
            if self.dicIndustry.has_key(sIndustry):
                self.dicIndustry[sIndustry] = self.dicIndustry[sIndustry] + diccapital[key]/10000
            else:
                self.dicIndustry[sIndustry] =diccapital[key]/10000

        sortcaptital= sorted(dicValue.items(), key=lambda d:d[1], reverse = False)
        for i in sortcaptital:
            self.x.append(i[0])
            self.y.append(i[1]/10000)


        dcap = 0
        for cap in diccapital:
            if cap != 'total':
                dcap = dcap + diccapital[cap]
        self.y3 = [data*abs(capital)/10000]
        self.y4 = [capital/10000,dcap/10000]

        for alpha in self.x6:
            dTotalVaR = VaR_sim(dfdata,alpha)
            self.y6.append(dTotalVaR*abs(capital)/10000)

        sortcaptital= sorted(diccapital.items(), key=lambda d:d[1], reverse = True)
        sortindustry = sorted(self.dicIndustry.items(),key=lambda d:d[1], reverse = True)
        for i in sortcaptital:
             self.x1.append(i[0])
             self.y1.append(i[1]/10000)
        for i in sortindustry:
            self.x5.append(i[0])
            self.y5.append(i[1])

        self.c.closeApp.emit(alpha1)


    def clickedbutton(self):
        #self.eventEngine.register(EVENT_TIMER,self.pintdatas)
        event = Event("showData")
        self.eventEngine.put(event)


    def emitSignal(self,alpha):
        self.l.clear()
        self.l.nextRow()
        title = 'VaR-'+ str(alpha)
        self.p1 = self.plotBarGraphItem(title,self.x,self.y)    #VaR
        self.l.addItem(self.p1)

        self.l.nextRow()
        self.p2 = self.plotBarGraphItem(U'持仓市值',self.x1,self.y1)
        self.l.addItem(self.p2)

        self.l2.clear()
        self.l2.nextRow()
        title = U'组合VaR'
        self.p3 = self.plotLineGraphItem(title,self.x6,self.y6)
        self.l2.addItem(self.p3)

        #self.p3 = self.plotBarGraphItem(title,self.x3,self.y3)
        #self.l2.addItem(self.p3)

        self.l2.nextRow()
        self.p4 = self.plotBarGraphItem(U'总持仓市值',self.x4,self.y4)
        self.l2.addItem(self.p4)

        self.l2.nextRow()
        self.p5 = self.plotBarGraphItem(U'行业分布',self.x5,self.y5)
        self.l2.addItem(self.p5)

        self.setLayout(self.lastb)




## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    # 界面设置
    cfgfile = QtCore.QFile('css.qss')
    cfgfile.open(QtCore.QFile.ReadOnly)
    styleSheet = cfgfile.readAll()
    styleSheet = unicode(styleSheet, encoding='utf8')
    app.setStyleSheet(styleSheet)
    ee = EventEngine()
    ui = TestWidget(ee)
    ui.showMaximized()
    app.exec_()
