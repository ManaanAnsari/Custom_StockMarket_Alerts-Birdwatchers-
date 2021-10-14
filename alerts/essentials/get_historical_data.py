#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 17:14:58 2020

@author: manaan
"""

from datetime import datetime,timedelta,date,time
import pandas as pd
from time import sleep
from alpha_vantage.timeseries import TimeSeries
import numpy as np
from .global_variables import mongo_connection_string
from pymongo import MongoClient
import yfinance as yf

'''
note:   historical data @ Zerodha costs 2k extra 
        hence using free alphavantage API
'''

def pullData(tickerlist,start=None,end=None,interval = '1m'):
    '''interval - Time interval between two consecutive data points in the time series. 
    The following values are supported: 1min, 5min, 15min, 30min, 60min'''
    NSEdata = {}
    data_pulled = False
    for ticker in tickerlist:
        print("pulling "+ticker)
        try:
            symbol=ticker + '.NS'
            if ticker == 'NIFTY50':
                symbol = '^NSEI'
            elif ticker == 'BANKNIFTY':
                symbol = '^NSEBANK'
            if start is None:
                start = date.today()
            if end is None:
                end = start +timedelta(days=1)
            stockdata = yf.download(tickers=symbol, start=start, end=end, interval=interval)
            if len(stockdata):
                data_pulled = True
        except Exception as e :
            print(e)
            data_pulled = False
            continue

        if data_pulled:
            # rename columns of stockdata to match earlier Quandl output
            stockdata.reset_index(inplace=True)
            stockdata["timestamp"] = stockdata["Datetime"].dt.tz_localize(None)
            stockdata.drop('Close', axis=1, inplace=True)
            stockdata.drop('Datetime', axis=1, inplace=True)
            stockdata.rename(columns={"Open": "open", "High": "high", "Low": "low", "Adj Close": "close","Volume": "volume"} ,inplace=True)
            NSEdata[ticker] = stockdata
            #break
    return NSEdata


