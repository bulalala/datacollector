# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import *
from uiOpenInt import TestWidget
from ui_statistic_openint import StatisticWidget
from eventEngine import *
from ui.ui_spread_widgets import SpreadWidget

class TabDemo(QTabWidget):
    def __init__(self, parent=None):
        super(TabDemo, self).__init__(parent)
        ee = EventEngine()
        ee1 = EventEngine()
        ee2 = EventEngine()
        ui = TestWidget(ee)
        self.tab1 = ui
        self.tab2 = StatisticWidget(ee1)
        self.tab3 = SpreadWidget(ee)
        ee.start()

        self.addTab(self.tab1, "持仓分布")
        self.addTab(self.tab2, "历史统计")
        self.addTab(self.tab3, "配对分析")
        self.setTabPosition(QTabWidget.West)

        self.setWindowTitle("持仓分析")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = TabDemo()
    demo.showMaximized()
    sys.exit(app.exec_())
