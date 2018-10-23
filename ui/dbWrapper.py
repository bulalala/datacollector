# encoding: UTF-8
import psycopg2
import pandas as pd
import pyqtgraph as pg
import matplotlib.pyplot as plt
from cnsort import cnsort

class dbWrapper:
    def __init__(self,shost):
        self.conn = psycopg2.connect(host=shost, port=59813, user='root', password='sq2018@sh!', database='history_et_db')
        self.cur = self.conn.cursor()

        self.conn_real = psycopg2.connect(host=shost, port=59813, user='root', password='sq2018@sh!', database='real_db')
        self.cur_real = self.conn_real.cursor()

    def getBars(self,sSymbol,sBDay,sEDay,sBarType):
        try:
            sSQL = "select tradingday, bartime, openprice, highprice, lowprice, closeprice, volume,openinterest from china_fut." + sSymbol + " where tradingday >= %s  and tradingday <= %s and bartype = %s  and bartime >= %s and bartime <= %s order by tradingday,id asc;"
            self.cur.execute(sSQL,(str(sBDay),str(sEDay),sBarType,'08:00','16:00'))
            Bars = self.cur.fetchall()
            dfBars = pd.DataFrame(Bars)
            if len(dfBars)==0:
                return pd.DataFrame()
            dfBars.columns = ['tradingday', 'bartime', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume','openinterest']
            dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']] = dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']].astype(float)
            dfBars[['bartime']] = dfBars[['bartime']].astype(str)
            dfBars[['volume', 'openinterest']] = dfBars[['volume', 'openinterest']].astype(int)
            dfBars[['tradingday']] = dfBars[['tradingday']].astype(str)
            return dfBars
        except:
            self.__init__('postgres-g2mc86ry.sh.cdb.myqcloud.com')
            return pd.DataFrame()

    def getNightBars(self,sSymbol,sBDay,sEDay,sBarType):
        sSQL = "select tradingday, bartime, openprice, highprice, lowprice, closeprice, volume from china_fut." + sSymbol + " where tradingday >= %s  and tradingday <= %s and bartype = %s  and (bartime >= %s or bartime <= %s) order by tradingday,id asc;"
        self.cur.execute(sSQL,(str(sBDay),str(sEDay),sBarType,'20:00','02:31'))
        Bars = self.cur.fetchall()
        dfBars = pd.DataFrame(Bars)
        if len(dfBars)==0:
            return pd.DataFrame()
        dfBars.columns = ['tradingday', 'bartime', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume']
        dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']] = dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']].astype(float)
        dfBars[['bartime']] = dfBars[['bartime']].astype(str)
        return dfBars

    def getBarsbyDay(self,sSymbol):
        sSQL = "select tradingday, bartime, openprice, highprice, lowprice, closeprice, volume from china_fut." + sSymbol + " where bartype = %s and bartime >= %s and bartime <= %s order by tradingday asc;"
        self.cur.execute(sSQL, ('Daily','08:00','16:00',))
        Bars = self.cur.fetchall()
        dfBars = pd.DataFrame(Bars)
        dfBars.columns = ['tradingday', 'bartime', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume']
        dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']] = dfBars[['openprice', 'highprice', 'lowprice', 'closeprice']].astype(float)
        return dfBars

    def getContractbyProductID(self,sProductID):
        sSQL = "select symbol from china_fut.contract_all  where productid = %s  order by symbol asc;"
        self.cur.execute(sSQL, (sProductID,))
        Datas = self.cur.fetchall()
        dfDatas = pd.DataFrame(Datas)
        dfDatas.columns = ['symbol']
        dfDatas[['symbol']] = dfDatas[['symbol']].astype(str)
        return dfDatas

    def getContractWeight(self,sProductID):
        sSQL = "select tradingday, weight from china_fut.contract_weight where productID = %s order by tradingday asc;"
        self.cur.execute(sSQL, (sProductID,))
        Bars = self.cur.fetchall()
        dfBars = pd.DataFrame(Bars)
        dfBars.columns = ['tradingday', 'weight']
        dfBars[['weight']] = dfBars[['weight']].astype(float)
        dfBars[['tradingday']] = dfBars[['tradingday']].astype(str)
        return dfBars

    def getSettlementPrice(self,sSymbol,tradingday):
        try:
            sSQL = "select presettlementprice, settlementprice from china_fut.contract_" + tradingday + " where symbol = %s ;"
            self.cur_real.execute(sSQL, (sSymbol,))
            Bars = self.cur_real.fetchall()
            dfBars = pd.DataFrame(Bars)
            dfBars.columns = ['presettlementprice', 'settlementprice']
            dfBars[['presettlementprice', 'settlementprice']] = dfBars[['presettlementprice', 'settlementprice']].astype(float)
            return dfBars.iloc[0]
        except:
            self.__init__()
            return

    def getAllSettlementPrice(self,tradingday):
        try:
            sSQL = "select symbol,settlementprice,multipler from china_fut.contract_" + tradingday + " order by productid asc;"
            self.cur_real.execute(sSQL, ())
            Bars = self.cur_real.fetchall()
            dfBars = pd.DataFrame(Bars)
            dfBars.columns = ['symbol', 'settlementprice','multipler']
            dfBars[['symbol']] = dfBars[['symbol']].astype(str)
            dfBars[['settlementprice','multipler']] = dfBars[['settlementprice','multipler']].astype(float)
            return dfBars
        except:
            self.__init__()
            return

    def getTradeSymbol_productid(self,sProductid,tradingday):
        try:
            sSQL = "select symbol from china_fut.contract_" + tradingday + " where productid = %s order by symbol asc ;"
            self.cur_real.execute(sSQL, (sProductid,))
            Bars = self.cur_real.fetchall()
            dfBars = pd.DataFrame(Bars)
            dfBars.columns = ['symbol']
            dfBars[['symbol']] = dfBars[['symbol']].astype(str)
            return dfBars
        except:
            self.__init__()
            return

    def highprice(self, x):
        if x['highprice_y'] > x['highprice_x']:
            return x['highprice_y']
        else:
            return x['highprice_x']

    def lowprice(self, x):
        if x['lowprice_y'] < x['lowprice_x']:
            return x['lowprice_y']
        else:
            return x['lowprice_x']

    def openprice(self, x):
        if pd.isnull(x['openprice_y']):
            return x['openprice_x']
        else:
            return x['openprice_y']

    def getFullDayBars(self, sSymbol, sBDay, sEDay):
        nightbar = self.getNightBars(sSymbol, sBDay, sEDay, 'Daily')
        daybar = self.getBars(sSymbol, sBDay, sEDay, 'Daily')
        if len(nightbar) == 0:
            return daybar
        bar = pd.merge(daybar, nightbar, how='left', on=['tradingday'])
        bar['openprice'] = bar.apply(self.openprice,axis=1)
        bar['highprice'] = bar.apply(self.highprice,axis=1)
        bar['lowprice'] = bar.apply(self.lowprice,axis=1)
        bar['closeprice'] = bar['closeprice_x']
        bar = bar[['tradingday', 'bartime_x', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume_x']]
        bar.columns = ['tradingday', 'bartime', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume']
        return bar

    def getExchangePositon(self,sTradingDay,sProdctid,sSymbol,sType):
        sSQL = "select tradingday, rank, quatity, change from china_fut.Contract_openint_dce2 where tradingday = %s and productid = %s and symbol = %s and ranktype = %s order by tradingday, rank asc;"
        self.cur.execute(sSQL, (sTradingDay,sProdctid,sSymbol,sType,))
        df = self.cur.fetchall()
        df = pd.DataFrame(df)
        if len(df) == 0:
            return df
        df.columns = ['tradingday','rank','quatity','change']
        df[['tradingday']] = df[['tradingday']].astype(str)
        df[['rank']] = df[['rank']].astype(int)
        df[['quatity','change']] = df[['quatity','change']].astype(float)
        return  df

    def getExchangePositon_czce(self,sTradingDay,sProdctid,sSymbol,sType):
        sSQL = "select tradingday, rank, quatity, change from china_fut.Contract_openint_czce where tradingday = %s and productid = %s and symbol = %s and ranktype = %s order by tradingday, rank asc;"
        self.cur.execute(sSQL, (sTradingDay,sProdctid,sSymbol,sType,))
        df = self.cur.fetchall()
        df = pd.DataFrame(df)
        if len(df) == 0:
            return df
        df.columns = ['tradingday','rank','quatity','change']
        df[['tradingday']] = df[['tradingday']].astype(str)
        df[['rank']] = df[['rank']].astype(int)
        df[['quatity','change']] = df[['quatity','change']].astype(float)
        return  df

    def getTradingSymbol(self,sProdctid):
        sSQL = "select distinct tradingday,symbol from china_fut.Contract_openint_czce where  productid = %s and symbol != %s order by tradingday asc;"
        self.cur.execute(sSQL, (sProdctid,'all',))
        df = self.cur.fetchall()
        df = pd.DataFrame(df)
        df.columns = ['tradingday','symbol']
        return df

    def getTradingDay(self):
        sSQL = "select distinct tradingday from china_fut.contract_sort order by tradingday asc;"
        self.cur.execute(sSQL,())
        TradingDay = self.cur.fetchall()
        TradingDay = pd.DataFrame(TradingDay)
        TradingDay.columns = ['tradingday']
        TradingDay[['tradingday']] = TradingDay[['tradingday']].astype(str)
        return TradingDay

    def getLstTradingDay(self):
        dfday = self.getTradingDay()
        if len(dfday) <= 0:
            return ""
        else:
            return dfday.tail(1).iat[0,0]

    def createactualinfotable(self):
        sSQL = "create table if not exists china_fut.Contract_Actual (TradingDay varchar(8), ProductID varchar(30),ActPrice numeric, PRIMARY KEY(TradingDay, ProductID));"
        self.cur.execute(sSQL)
        self.conn.commit()

    def createopinteresttable(self):
        sSQL = "create table if not exists china_fut.Contract_openint_dce2 (TradingDay varchar(8), ProductID varchar(30),Symbol varchar(30),Exchange varchar(10),Rank integer,Company varchar(30),Quatity numeric,Change numeric,Ranktype varchar(8));"
        self.cur.execute(sSQL)
        self.conn.commit()

    def insertactionprice(self,stradingday,sql):
        # 插入之前先删除数据
        sSQL = "delete from china_fut.Contract_Actual where Tradingday = %s"
        self.cur.execute(sSQL, (stradingday,))
        self.conn.commit()
        sSQL = "insert into china_fut.Contract_Actual (TradingDay, ProductID, ActPrice) values " + sql + ";"
        self.cur.execute(sSQL)
        self.conn.commit()

    def insertopeninterest(self,stradingday,sql,exchange,table):
        # 插入之前先删除数据
        sSQL = "delete from china_fut." + table+" where Tradingday = %s and exchange = %s"
        self.cur.execute(sSQL, (stradingday,exchange,))
        self.conn.commit()
        sSQL = "insert into china_fut."+ table +" (TradingDay, ProductID, Symbol,Exchange, Rank, Company, Quatity, Change, Ranktype) values " + sql + ";"
        self.cur.execute(sSQL)
        self.conn.commit()

###############################交易所公布数据调用接口###############################
    def getDataBySeat(self,seat,stradingday):
        dfLong = pd.DataFrame()
        dfShort = pd.DataFrame()
        #获取某席位数据
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_shfe where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #DCE
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_dce where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #CZCE
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_czce where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #获取SHFE席位数据
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_shfe where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        #DCE
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_dce where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        #czce
        sSQL = U'select tradingday, productid, symbol, quatity from china_fut.contract_openinterest_czce where tradingday = %s  and company like %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'%'+seat+'%','short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        if len(dfShort) == 0 or len(dfLong) == 0:
            return pd.DataFrame()
        dfShort.columns = ['tradingday', 'productid', 'symbol', 'quatity']
        dfLong.columns = ['tradingday', 'productid', 'symbol', 'quatity']
        dfdata = pd.merge(dfLong,dfShort,on=['tradingday', 'productid', 'symbol'],how='outer')
        dfdata = dfdata.fillna(0)
        dfdata.columns = ['tradingday', 'productid', 'symbol', 'long','short']
        dfdata = dfdata.sort_values(by = 'symbol',axis = 0,ascending = True)
        dfdata.index = range(0,len(dfdata))
        dfdata['quatity'] = dfdata['long'] - dfdata['short']
        dfdata[['long','short','quatity']] = dfdata[['long','short','quatity']].astype(float)
        return dfdata

    def getDataByTradingday(self,stradingday):
        dfLong = pd.DataFrame()
        dfShort = pd.DataFrame()
        #SHFE
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_shfe where tradingday = %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #DCE
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_dce where tradingday = %s  and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #CZCE
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_czce where tradingday = %s  and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'long','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfLong = dfLong.append(dfdatas)
        #获取SHFE席位数据
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_shfe where tradingday = %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        #DCE
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_dce where tradingday = %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        #czce
        sSQL = U'select tradingday, productid, symbol, quatity,company from china_fut.contract_openinterest_czce where tradingday = %s and ranktype = %s and symbol != %s order by productid,symbol asc;'
        self.cur.execute(sSQL,(stradingday,'short','all'))
        datas = self.cur.fetchall()
        dfdatas = pd.DataFrame(datas)
        dfShort = dfShort.append(dfdatas)
        if len(dfShort) == 0 or len(dfLong) == 0:
            return pd.DataFrame()
        dfShort.columns = ['tradingday', 'productid', 'symbol', 'quatity','company']
        dfLong.columns = ['tradingday', 'productid', 'symbol', 'quatity','company']
        dfdata = pd.merge(dfLong,dfShort,on=['tradingday', 'productid', 'symbol','company'],how='outer')
        dfdata = dfdata.fillna(0)
        dfdata.columns = ['tradingday', 'productid', 'symbol', 'long','company','short']
        dfdata = dfdata.sort_values(by = 'symbol',axis = 0,ascending = True)
        dfdata.index = range(0,len(dfdata))
        dfdata['quatity'] = dfdata['long'] - dfdata['short']
        dfdata[['long','short','quatity']] = dfdata[['long','short','quatity']].astype(float)
        return dfdata

    def getAllCompany(self):
        # 插入之前先删除数据
        sSQL = "select distinct company from china_fut.contract_openinterest_czce"
        self.cur.execute(sSQL, ())
        datas = self.cur.fetchall()
        df_czce = pd.DataFrame(datas)
        df_czce.columns = ['company']

        sSQL = "select distinct company from china_fut.contract_openinterest_dce"
        self.cur.execute(sSQL, ())
        datas = self.cur.fetchall()
        df_dce = pd.DataFrame(datas)
        df_dce.columns = ['company']

        sSQL = "select distinct company from china_fut.contract_openinterest_shfe"
        self.cur.execute(sSQL, ())
        datas = self.cur.fetchall()
        df_shfe = pd.DataFrame(datas)
        df_shfe.columns = ['company']

        df = pd.merge(df_czce,df_dce,on=['company'],how='outer')
        df = pd.merge(df,df_shfe,on=['company'],how='outer')
        companies = df['company'].values.tolist()
        companies = cnsort(companies)
        return companies

    def getOpenIntTradingDay(self):
        sSQL = "select distinct tradingday from china_fut.contract_openinterest_shfe order by tradingday asc;"
        self.cur.execute(sSQL,())
        TradingDay = self.cur.fetchall()
        TradingDay = pd.DataFrame(TradingDay)
        TradingDay.columns = ['tradingday']
        TradingDay[['tradingday']] = TradingDay[['tradingday']].astype(str)
        return TradingDay

    def create_openint_index_table(self):
        sSQL = "create table if not exists china_fut.contract_openint_index (TradingDay varchar(8), Company varchar(30), ProductID varchar(30),Symbol varchar(30),MarketValue numeric,long_rank INTEGER ,short_rank INTEGER, PRIMARY KEY(TradingDay, Company,ProductID,Symbol));"
        self.cur.execute(sSQL)
        self.conn.commit()

    def batchup_openint_index(self,dfdata):
        svalues = ''
        for i in range(0, len(dfdata)):
            val = "('" + dfdata.loc[i,'tradingday'] + "', " + "'" + dfdata.loc[i,'company'] + "', " + "'" + dfdata.loc[i,'productid'] + "', "+ "'" + dfdata.loc[i,'symbol'] + "', "+ "'" + str(dfdata.loc[i,'marketvalue']) + "')"
            if svalues == '':
                svalues = val
            else:
                svalues = svalues + ',' + val
        sql =  'insert into china_fut.contract_openint_index(tradingday, company, productid,symbol,marketvalue) values ' + svalues + 'on conflict(tradingday, company, productid,symbol) do nothing;'
        self.cur.execute(sql)
        self.conn.commit()

    def batchup_openint_index2(self,dfdata):
        svalues = ''
        for i in range(0, len(dfdata)):
            val = "('" + dfdata.loc[i,'tradingday'] + "', " + "'" + dfdata.loc[i,'company'] + "', " + "'" + dfdata.loc[i,'productid'] + "', "+ "'" + dfdata.loc[i,'symbol'] + "', "+ "'" + str(dfdata.loc[i,'marketvalue']) + "', "+ "'" + str(dfdata.loc[i,'long_rank'])+ "', "+ "'" + str(dfdata.loc[i,'short_rank']) + "')"
            if svalues == '':
                svalues = val
            else:
                svalues = svalues + ',' + val
        sql =  'insert into china_fut.contract_openint_index(tradingday, company, productid,symbol,marketvalue,long_rank,short_rank) values ' + svalues + 'on conflict(tradingday, company, productid,symbol) do nothing;'
        self.cur.execute(sql)
        self.conn.commit()

    def get_marketvalue_byproductid(self,productid,company):
        sSQL = "select tradingday,marketvalue from china_fut.contract_openint_index where productid = %s and company like %s and symbol = %s order by tradingday asc;"
        self.cur.execute(sSQL,(productid,'%'+company+'%','all'))
        data = self.cur.fetchall()
        dfdata = pd.DataFrame(data)
        if len(dfdata) == 0:
            return dfdata
        dfdata.columns = ['tradingday','marketvalue']
        dfdata[['tradingday']] = dfdata[['tradingday']].astype(str)
        dfdata[['marketvalue']] = dfdata[['marketvalue']].astype(float)
        return dfdata

    def get_marketvalue_by_longrank(self,productid,irank):
        sSQL = "select tradingday,marketvalue,company from china_fut.contract_openint_index where productid = %s and long_rank <= %s and symbol = %s order by tradingday asc;"
        self.cur.execute(sSQL,(productid,irank,'all'))
        data = self.cur.fetchall()
        dfdata = pd.DataFrame(data)
        if len(dfdata) == 0:
            return dfdata
        dfdata.columns = ['tradingday','marketvalue','company']
        dfdata[['tradingday','company']] = dfdata[['tradingday','company']].astype(str)
        dfdata[['marketvalue']] = dfdata[['marketvalue']].astype(float)
        return dfdata

    def get_marketvalue_by_shortrank(self,productid,irank):
        sSQL = "select tradingday,marketvalue,company from china_fut.contract_openint_index where productid = %s and short_rank <= %s and symbol = %s order by tradingday asc;"
        self.cur.execute(sSQL,(productid,irank,'all'))
        data = self.cur.fetchall()
        dfdata = pd.DataFrame(data)
        if len(dfdata) == 0:
            return dfdata
        dfdata.columns = ['tradingday','marketvalue','company']
        dfdata[['tradingday','company']] = dfdata[['tradingday','company']].astype(str)
        dfdata[['marketvalue']] = dfdata[['marketvalue']].astype(float)
        return dfdata



def plotBarGraphItem(name,lstX=[],lstY=[]):
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
    

if __name__ == '__main__':
    db = dbWrapper('postgres-a1mzuj9c.sql.tencentcdb.com')
    data = db.getAllCompany()
    print(data)
    data = db.getDataBySeat(U'永安期货','20180725')
    settlementprice = db.getAllSettlementPrice('20180725')
    df = pd.merge(data,settlementprice,on=['symbol'],how='left')
    df['marketvalue'] = df['quatity']*df['settlementprice']*df['multipler']/10000
    num_list = df['marketvalue'].values.tolist()
    plt.bar(range(len(num_list)), num_list)
    plt.show()


    """
    db.getDataBySeat(U'格林大华','20180710')
    db.getAllCompany()
    settlementprice = db.getAllSettlementPrice('20180725')
    openint = db.getDataBySeat(U'永安期货','20180725')
    df = pd.merge(openint,settlementprice,on=['symbol'],how='left')
    df['marketvalue'] = df['quatity']*df['settlementprice']/10000
    grouped = df['marketvalue'].groupby(df['productid']).sum()
    ix = []
    index = []
    values = []
    i = 0
    for productid in grouped.index:
        ix.append(i)
        index.append(productid)
        values.append(grouped[productid])
        i = i + 1
    print values

    win = pg.plot()
    win.setWindowTitle('pyqtgraph example: BarGraphItem')
    bg1 = pg.BarGraphItem(x=ix, height=values, width=0.3, brush='r')
    #win.addItem(bg1)
    p = plotBarGraphItem('test',index,values)
    win.addItem(p)

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    """




