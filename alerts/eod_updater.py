
from datetime import datetime,timedelta,date,time
from pymongo import MongoClient
import pandas as pd
import numpy as np
import requests

from essentials.instrument_dict import instruments_dict
from essentials.global_variables import mongo_connection_string
from essentials.get_historical_data import pullData
from email_notifier import generate_report
from helper import *


'''
this file updates the historical data in our db 
todo: make it inteligent i.e if historical collection is empty store all the data pulled from alphavantage 
note: this code 'll be removed once we purchase zerodha's historical

'''



def updateHistoricalData():
    print('updating historical data')
    d = datetime.now()
    if (d.isoweekday() not in range(1, 6)): # only run mon-fri check for market open here too 
        return False
    # get tickerist
    tickerlist = list(instruments_dict.values())
    # connect to db
    client = MongoClient(mongo_connection_string)
    # get database object
    db = client.Historical_Data
    '''dont store or execute if todays data already present'''
    # get a collection to check if the function is already executed
    collection = db[tickerlist[0]]
    # get latest row from collection
    latest = collection.find_one(sort=[('timestamp', -1)])
    # check if todays data present
    if latest:
        if latest['timestamp'].day == datetime.today().day:
            return False
    ''' todays data not present '''
    # pull data from alphavantage (takes time ~ 10 mins for 20 stocks)
    # data = pullData(tickerlist,50000000,'1min')
    print('pulling data from 3rd party')
    data = pullData(tickerlist,None,None,'1m')
    # store data
    for collection_name, df in data.items():
        # make a copy of db (staying safe) and do necessary operations
        temp_df = df.copy()
        temp_df.reset_index(inplace=True)
        temp_df.rename(columns={"date_india": "timestamp"} ,inplace=True)
        temp_df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close","Volume": "volume"} ,inplace=True)
        # get only todays data
        temp_df = temp_df.loc[temp_df['timestamp'] > pd.Timestamp('today').floor('D')]
        # temp_df['data_source'] = 'Alpha Vantage'
        temp_df['data_source'] = 'Yahoo Finance'
        
        # get summarized live data too..
        db = client.Zerodha_LiveData
        # get collection object
        collection = db[collection_name]
        
        query = {
                "timestamp": {
                    "$gte":datetime.combine(date.today(),time(9,15)),
                    "$lt":datetime.combine(date.today(),time(15,30))
                }
            }
        live_data =  pd.DataFrame(list(collection.find(query)))
        if len(live_data):
            live_data.set_index('timestamp',inplace=True)
            ohlc = live_data['last_price'].resample('1min').ohlc()
            ohlc['volume_f'] = live_data['volume'].resample('1min').first()
            ohlc['volume_l'] = live_data['volume'].resample('1min').last()
            ohlc['volume'] = ohlc['volume_l'] - ohlc['volume_f']
            ohlc.drop(columns=['volume_f', 'volume_l'],inplace=True)
            ohlc.dropna(inplace=True)
            ohlc.reset_index(inplace=True)
            ohlc['data_source'] = 'Zerodha'
            if len(temp_df) <= len(ohlc):
                print('we probably have correct Zerodha data so using that')
                temp_df = ohlc.copy()
                print('choosing zerodha')
        
        if len(temp_df):
            db = client.Historical_Data
            # get collection object
            collection = db[collection_name]
            # a dict format to store in mongo
            temp_dict = temp_df.to_dict('records')
            # insert in db
            collection.insert_many(temp_dict)
        print(collection_name+' historical saved')
    client.close()
    # done updating historical
    # now generate todays perfomance report
    generate_report()
    return True













