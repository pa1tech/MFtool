import numpy as np
import os, re, io, requests, openpyxl
import pandas as pd
from urllib.request import urlopen
from datetime import date,datetime
from scipy import optimize

# Glocal VARs
currDate = datetime(2024, 5, 3)
file = "mf_transactions.csv"

# Functions
def xnpv(rate,cashflows):
    chron_order = sorted(cashflows, key = lambda x: x[0])
    t0 = chron_order[0][0]
    return sum([float(cf)/(1+rate)**((t-t0).days/365.0) for (t,cf) in chron_order])

def xirr(cashflows,currDate,current,guess=0.1):
	for i in range(len(cashflows)):
		t = np.array(cashflows[i][0].split('-'),dtype=int)
		#cashflows[i][0] = cashflows[i][0] #date(t[0],t[1],t[2])
		cashflows[i][0] = datetime.strptime(cashflows[i][0], "%Y-%m-%d") 
	cashflows.append((currDate,-current))
	return optimize.newton(lambda r: xnpv(r,cashflows),guess)

def getNifty(date):
	url="https://archives.nseindia.com/content/indices/ind_close_all_%s.csv"%date.strftime("%d%m%Y")
	s=requests.get(url).content
	indicesDf=pd.read_csv(io.StringIO(s.decode('utf-8')))
	indicesDf = indicesDf.loc[indicesDf['Index Name'] == 'Nifty 50']
	niftyClose = indicesDf.at[0,'Closing Index Value']
	return float(niftyClose)

mfTxt = urlopen("https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?tp=1&frmdt=%s-%s-%s"%(currDate.strftime("%d"),currDate.strftime("%b"),currDate.strftime("%Y")))
mfTxt = str(mfTxt.read())
def getNAVbyISIN(isin):
	x = re.findall(";%s;;.*?;;;"%str(isin), mfTxt)
	if(len(x)>0): return float(x[0].split(';;')[1])
	else: return 0

currNifty = getNifty(currDate)
pwd = os.path.dirname(os.path.realpath(__file__))

# Data Aggregation
data = pd.read_csv(pwd+'/'+file)
data1 = pd.read_csv(pwd+'/'+file)
data['days'] = np.zeros(len(data['isin']))
data['Current NAV'] = np.zeros(len(data['isin']))
data['Absolute Return Nifty Equiv'] = np.zeros(len(data['isin'])) 

data['trade_date'] = pd.to_datetime(data['trade_date'])
data['trade_date'] = data['trade_date'].dt.strftime('%Y-%m-%d')


for i in range(len(data['isin'])):
	fund = data.at[i,'isin'] 
	#buyDate = np.array(data['trade_date'][i].split('-'),dtype=int)

	buyDate = datetime.strptime(data['trade_date'][i], "%Y-%m-%d") 
	data.at[i,'days'] = (currDate-buyDate).days #(currDate-date(buyDate[0],buyDate[1],buyDate[2])).days
	data.at[i,'Current NAV'] = getNAVbyISIN(fund)
	
	#niftyPrice = getNifty(date(buyDate[0],buyDate[1],buyDate[2]))
	if(str(data.at[i,'NIFTY']) != "nan"):
		niftyPrice = float(data.at[i,'NIFTY'])
	else:
		niftyPrice = getNifty(buyDate)
		data1.at[i,'NIFTY'] = niftyPrice
	data.at[i,'Absolute Return Nifty Equiv'] = 100*(currNifty-niftyPrice)/niftyPrice

data['Absolute Return'] = 100*(data['Current NAV']-data['price'])/data['price']


# Summary
summaryDf = pd.DataFrame()
with pd.ExcelWriter(pwd+'/MF_Report.xlsx', engine='openpyxl') as writer:
	for fund in data.symbol.unique():
		print(fund)
		fundDf = (data.loc[data['symbol'] == fund]).copy()
		#print(fundDf.head())

		fundDf['invested'] = fundDf['quantity']*fundDf['price']
		fundDf['current'] = fundDf['quantity']*fundDf['Current NAV']
		invested = fundDf['invested'].sum()
		current = fundDf['current'].sum()

		fundDf['weightedDays'] = fundDf['quantity']*fundDf['price']*fundDf['days']/invested
		fundDf['weighted Absolute Return'] = fundDf['quantity']*fundDf['price']*fundDf['Absolute Return']/invested
		fundDf['weighted Absolute Return Nifty Equiv.'] = fundDf['quantity']*fundDf['price']*fundDf['Absolute Return Nifty Equiv']/invested
		
		weightedDays = fundDf['weightedDays'].sum()
		weightedPerc = fundDf['weighted Absolute Return'].sum()
		weightedNiftyPerc = fundDf['weighted Absolute Return Nifty Equiv.'].sum()

		xirrFund = 100*xirr(((fundDf[["trade_date", "invested"]]).values.tolist()),currDate,current)
		xirrNifty = 100*xirr(((fundDf[["trade_date", "invested"]]).values.tolist()),currDate,invested*(1+weightedNiftyPerc/100))

		newRow = pd.DataFrame({'Fund': fund, 
								'Invested': invested, 
								'Current': current, 
								'Avg. Days Invested':weightedDays,
								'Absolute Return': weightedPerc,
								'Absolute Return - Nifty Equiv.': weightedNiftyPerc,
								'XIRR': xirrFund,
								'XIRR - Nifty Equiv.': xirrNifty}, index = [0])

		summaryDf = pd.concat([summaryDf,newRow])

		fundDf = fundDf.round(decimals = 3)
		fundDf.to_excel(writer,sheet_name=fund[:31],index=False)

	#%%
	data['invested'] = data['quantity']*data['price']
	data['current'] = data['quantity']*data['Current NAV']
	invested = data['invested'].sum()
	current = data['current'].sum()

	data['weightedDays'] = data['quantity']*data['price']*data['days']/invested
	data['weighted Absolute Return'] = data['quantity']*data['price']*data['Absolute Return']/invested
	data['weighted Absolute Return Nifty Equiv.'] = data['quantity']*data['price']*data['Absolute Return Nifty Equiv']/invested
	
	weightedDays = data['weightedDays'].sum()
	weightedPerc = data['weighted Absolute Return'].sum()
	weightedNiftyPerc = data['weighted Absolute Return Nifty Equiv.'].sum()

	xirrFund = 100*xirr(((data[["trade_date", "invested"]]).values.tolist()),currDate,current)
	xirrNifty = 100*xirr(((data[["trade_date", "invested"]]).values.tolist()),currDate,invested*(1+weightedNiftyPerc/100))

	newRow = pd.DataFrame({'Fund': "Overall", 
							'Invested': invested, 
							'Current': current, 
							'Avg. Days Invested':weightedDays,
							'Absolute Return': weightedPerc,
							'Absolute Return - Nifty Equiv.': weightedNiftyPerc,
							'XIRR': xirrFund,
							'XIRR - Nifty Equiv.': xirrNifty}, index = [0])

	summaryDf = pd.concat([summaryDf,newRow])

	summaryDf = summaryDf.round(decimals = 3)
	summaryDf.to_excel(writer,sheet_name='Summary',index=False)

summaryDf.to_excel(pwd+'/MF_Summary.xlsx',index=False)

data1.to_csv(pwd+"/"+file)