# encoding: UTF-8
__author__ = 'hyc'

import scipy.stats as stats
import pandas as pd
import sys
import re
import math
import numpy as np
#自己开发模块
from dbWrapper import dbWrapper

db = dbWrapper('postgres-fj7nqbmu.sql.tencentcdb.com')
dicVaR = {}
#计算Value at Risk 计算均值，方差
def VaR_norm(data,alpha=0.99,n=252):
    Z = stats.norm(0,1).ppf(1-alpha)    #反概率密度函数
    data['mean'] = pd.rolling_mean(data['return'],n)
    data['std'] = pd.rolling_std(data['return'],n)
    if math.isnan(data.tail(1).iat[0,3]):
        data['mean'] = pd.expanding_mean(data['return'])
        data['std'] = pd.expanding_std(data['return'])
    data['delta'] = data['mean'] + Z*data['std']
    return data.tail(1).iat[0,4]

#模拟法计算Value at Risk
def VaR_sim(data,alpha=0.99):
    return np.percentile(data['return'],(1-alpha)*100)#分位数

#计算收益率
def getReturn(productid):
    data = db.getBars(productid+'_0A',"20120101","20900101","Daily")
    weight = db.getContractWeight(productid)
    data = pd.merge(data,weight,on='tradingday')
    data['rcloseprice'] = data['closeprice'] + data['weight']
    data['precloseprice'] = data['closeprice'].shift(1)
    data['prercloseprice'] = data['rcloseprice'].shift(1)
    data['return'] = (data['rcloseprice'] - data['prercloseprice'])/data['precloseprice']
    return data[['tradingday','return']].dropna()

#根据权重计算portfolio
#input = {'rb':0.1,...,'ru':0.2}
def calPortfolioReturn(diccapital,capital,alpha=0.99):
    dicVaR.clear()
    dfdata = pd.DataFrame()
    for key in diccapital:
        productid = re.findall(r'[a-zA-Z]+', key)[0]
        dweight = diccapital[key]/capital
    #for i in range(0,len(lstproductid)):
        data = getReturn(productid)
        #计算单品种VaR
        curdata = data[['tradingday','return']]
        if diccapital[key] > 0:
            director = 1
        else:
            director = -1
        curdata['return'] = curdata['return']*director
        #dVaR = VaR_norm(curdata,0.95)
        dVaR = VaR_sim(curdata,alpha)
        dicVaR[key] = dVaR
        data = data[['tradingday','return']]
        if len(dfdata) == 0:
            dfdata = data
            dfdata['return'] = dfdata['return']*dweight
        else:
            dfdata = pd.merge(dfdata,data,on='tradingday',how='outer')
            dfdata = dfdata.fillna(0)
            dfdata['return'] = dfdata['return_x'] + dfdata['return_y']*dweight
            dfdata = dfdata[['tradingday','return']]
            dfdata = dfdata.sort_values(by='tradingday')
    dfdata.index = range(0,len(dfdata))
    return dfdata

def getconmulti(spid):
    if spid in ['ni', 'sn']:
        return 1
    elif spid in ['al', 'CF', 'cu', 'l', 'pb', 'pp',\
                  'SF', 'SM', 'TA', 'v', 'zn']:
        return 5
    elif spid in ['a', 'b', 'bu', 'c', 'cs', 'hc', 'jd', \
                  'm', 'MA', 'OI', 'p', 'rb', 'RM', 'RS',\
                  'ru', 'SR', 'WR', 'y','AP']:
        return 10
    elif spid in ['ag']:
        return 15
    elif spid in ['WH', 'FG', 'RI', 'JR', 'LR']:
        return 20
    elif spid in ['fu', 'PM']:
        return 50
    elif spid in ['jm']:
        return 60
    elif spid in ['ZC', 'j', 'i']:
        return 100
    elif spid in ['IC']:
        return 200
    elif spid in ['IF', 'IH']:
        return 300
    elif spid in ['fb', 'bb']:
        return 500
    elif spid in ['au','sc']:
        return 1000
    elif spid in ['TF', 'T']:
        return 10000

#通过csv读取仓位
def readCSV():
    lstsymbol = []
    lstpos = []
    data = pd.read_csv(U"持仓.csv",encoding = 'gbk')
    for i in range(0,len(data)):
        if len(data.iat[i,0])  > 8:
            continue
        lstsymbol.append(data.iat[i,0])     #合约
        if data.iat[i,1].find('买') == 0:  #方向
            lstpos.append(data.iat[i,2])    #持仓
        else:
            lstpos.append(-data.iat[i,2])

    return lstsymbol,lstpos

def getCaptital(lstsymbol,lstposition,tradingday):
    capital = 0
    diccapital = {}
    for i in range(0,len(lstsymbol)):
        data = db.getSettlementPrice(lstsymbol[i],tradingday)
        #capital = capital + data['presettlementprice']*getconmulti(re.findall(r'[a-zA-Z]+', lstsymbol[i])[0])*lstposition[i]
        if diccapital.has_key(lstsymbol[i]):
            diccapital[lstsymbol[i]] = diccapital[lstsymbol[i]] + data['settlementprice']*getconmulti(re.findall(r'[a-zA-Z]+', lstsymbol[i])[0])*lstposition[i]
        else:
            diccapital[lstsymbol[i]] = data['settlementprice']*getconmulti(re.findall(r'[a-zA-Z]+', lstsymbol[i])[0])*lstposition[i]
    for key in diccapital:
        capital = capital + abs(diccapital[key])
    return capital,diccapital


if __name__ == '__main__':
    lstsymbol,lstpos = readCSV()
    capital,diccapital = getCaptital(lstsymbol,lstpos,'20180426')
    data = calPortfolioReturn(diccapital,capital)
    data = VaR_sim(data,0.99)



