import requests, bs4, re, os
import numpy as np
import pandas as pd
from datetime import date

pwd = os.path.dirname(os.path.realpath(__file__))

file = "cams_mf.xlsx"
data = pd.read_excel(pwd+'/'+file, sheet_name="Sheet1")

# Extract ISIN from Groww website
def get_RTA_ISIN(rta_code, scheme_name):
    search = rta_code + " " + scheme_name.split("(")[0] + " groww"
    search = search.split(" ")
    search = "+".join(search)

    search = search.replace("&","%26")

    gSearch = requests.get('https://www.google.com/search?q='+search)
    soup = bs4.BeautifulSoup(gSearch.text,"html.parser")
    links = soup.find_all("a")


    for link in links:
        if( "groww.in" in link.get("href") ):
            growwUrl = requests.get("https://www.google.com"+link.get("href"))

            rtaCode = re.findall('"rta_scheme_code":".*",',growwUrl.text)
            rtaCode = rtaCode[0].split(':"')[1].split('",')[0]

            isin = re.findall('"isin":".*",',growwUrl.text)
            isin = isin[0].split(':"')[1].split('",')[0]

            schemeName = re.findall('"scheme_name":".*",',growwUrl.text)
            schemeName = schemeName[0].split(':"')[1].split('",')[0]
            schemeName = schemeName.replace(r"\u0026","&")

            if( rtaCode == rta_code):
                return isin,schemeName

mfISIN = {}
mfNAME = {}
toolMF = pd.DataFrame()

for i in range(len(list(data["PRODUCT_CODE"]))):
    if(data["PRODUCT_CODE"][i] not in mfISIN.keys()):

        isin,scheme_name = get_RTA_ISIN(data["PRODUCT_CODE"][i], data["SCHEME_NAME"][i])

        mfISIN[data["PRODUCT_CODE"][i]] = isin
        mfNAME[data["PRODUCT_CODE"][i]] = scheme_name

    newRow = pd.DataFrame({'symbol': mfNAME[data["PRODUCT_CODE"][i]], 
                            'isin': mfISIN[data["PRODUCT_CODE"][i]], 
                            'trade_date': data["TRADE_DATE"][i], 
                            'quantity':data["UNITS"][i],
                            'price': data["PRICE"][i],}, index = [0])

    toolMF = pd.concat([toolMF,newRow])

toolMF['trade_date'] = pd.to_datetime(toolMF['trade_date'])
#toolMF.at["trade_date"] = date.strftime("%d-%m-%Y")
toolMF['trade_date'] = toolMF['trade_date'].dt.strftime("%Y-%m-%d")
toolMF.to_csv(os.path.dirname(pwd)+"/mf_transactions.csv", index=False)