# -*- coding: utf-8 -*-
"""
Created on Sat May  6 18:02:13 2023

@author: apsin
"""
import creds #my credentials for API are stored
from jsonAPIcall import get_json_data 

import pandas as pd
import datetime

# Load the DataFrame with price and volume data for the S&P500 index

#df = pd.read_csv('sp500_data.csv')
dateFrom=  '1995-01-01'# '2015-01-01' 
dateTo=  datetime.date.today().strftime('%Y-%m-%d')  # '2019-12-31' 
indexSym= '^GSPC' # S&P500

#  '^GSPC' #S&P500
#'^DJI' #Dow Jones
# '^IXIC' # NASDAQ Composite
# '^RUT' # Russell 2000
# '^NSEI' #NIFTY 50
#'^NDX' #NASDAQ 100

url= "https://financialmodelingprep.com/api/v3/historical-price-full/index/{indexSym}?from={dateFrom}&to={dateTo}&apikey={my_api_key}".format(indexSym=indexSym, dateFrom= dateFrom, dateTo=dateTo, my_api_key=creds.my_api_key) 
df= pd.DataFrame(get_json_data(url)['historical'])
df= df[::-1] # reversing order of dataframe to make first entry be the dateFrom

df=df.reset_index().drop('index',axis=1)
# Bear market periods calculation---------------------------------------------------------------------------------------------------------------------------------
bear_market_threshold = 0.125 # 12.5- 15% drop captures bear market better 
df['pct_change'] = df['close'].pct_change().fillna(0)
df['cum_pct_change'] = (1 + df['pct_change']).cumprod() - 1
df['recent_high'] = df['close'].rolling(min_periods=1, window=510, center=False).max() # 2 x 260 business days per year
df['bear_market'] = ((df['recent_high']-df['close'])/df['close'])>= bear_market_threshold

#-----------------------------------------------------------------------------------------------------------------------------------------------------

# Define function to check if a given period is a rally
def is_rally(df, start_idx):
    end_idx = start_idx + 10 #rallies of concern restricted to periods of less than 10 days
    if end_idx >= len(df):
        return False
    first_close = df.loc[start_idx, 'close']
    
    if df.loc[start_idx, 'changePercent'] < 1: # if start day of rally is less than 1% rise than not relevant
        return False
    for i in range(start_idx+1, end_idx+1):
        if df.loc[i, 'close'] <= first_close: # not a rally if closing price in a consecutive rally day is lower than day 1 of rally
            return False
    return True

# Define function to check if a given day is a follow through day
def is_follow_through(df, idx):
    #if idx < 2 or idx > 9:
        #return False
    if df.loc[idx, 'changePercent'] < 1.35: # not a follow through if price change percent less than 1.25%
        return False
    prev_vol = df.loc[idx-1, 'volume']
    curr_vol = df.loc[idx, 'volume']
    if curr_vol <= prev_vol * 1.15: # if volume in a consecutive rally day is more than the day prior by 2% or more
        return False
    return True

df['rally'] = False
df['followThrough'] = False

# Loop through the DataFrame
for i in range(len(df)):
    if (df.loc[i,'bear_market']):
        if is_rally(df,i): # Check if current period is a bear market rally
            #print(i)
            df.loc[i, 'rally'] = True #record the start of every bear market rally
            for j in range(i+2, i+10):  # Loop through the next 3-10 days
                if is_follow_through(df, j):  # Check if one of the bear market rally days is a follow through day
                    df.loc[j, 'followThrough'] = True
                    print(j)
                
        

#export the data for import into PowerBI
df.to_excel('S&PHistoricalWithBear.xlsx',index= False)
