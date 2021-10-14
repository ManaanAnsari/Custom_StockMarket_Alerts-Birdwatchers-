from datetime import datetime,timedelta,date,time
import pandas as pd
import numpy as np
import os
import glob


'''
all helper functions that are less than 5/10 lines and are frequently reused is here 
'''

def round_candle(dt, direction, resolution):
    # this logic handles the roundoff for candles gt 60mins
    # basic logic is remove the extra hour and call roundoff with the remaining minute after 60 
    r = resolution
    to_use = dt
    if r > 60:
        '''
            this logic wont work cz every thing start after 9:15 'll have to use 'lll logic used for resampling 
            by adding 15 mins+ etc... figure it out b4 adding zerodha historical api
        '''
        diff = r - 60
        to_use = dt - timedelta(minutes=r)
        return round_minutes(to_use, direction, diff).replace(microsecond=0, second=0)
    else:
        return round_minutes(to_use, direction, r).replace(microsecond=0, second=0)
        
# a function that rounds off time either up or down
def round_minutes(dt, direction, resolution):
    new_minute = (dt.minute // resolution + (1 if direction == 'up' else 0)) * resolution
    return dt + timedelta(minutes=new_minute - dt.minute)

# a simple function that returns all the numbers in a string
def getNumTillChar(string):
    return int(''.join([s for s in string if s.isdigit()]))

# to check if market is still open this allows us to connect without cron
def check_if_market_open():
    d = datetime.now()
    if (d.isoweekday() in range(1, 6)) and ((d.time() >= time(9,15)) and (d.time() < time(15,31))):
        # if market open
        return True
    else:
        # if market close
        return False

# get format of filename and path saved
def getFilenamePKL(stock_name,candle):
    return './tempstorage/'+stock_name+'_'+candle+'_'+str(round_candle(datetime.now(), 'down', getNumTillChar(candle)).replace(microsecond=0, second=0))+'.pkl'

# using temprary storage and not requesting data everytime
def checkIfFetched(stock_name,candle):
    filename = getFilenamePKL(stock_name,candle)
    if os.path.isfile(filename):
        df = pd.read_pickle(filename)
        return df
    else:
        return []

def clearTempStorage():
    print('removing all pkl file')
    files = glob.glob('./tempstorage/*.pkl')
    for f in files:
        os.remove(f)
    return True



def RepresentsInt(s):
    # helper function to check if the given string can be converted to int
    try: 
        int(s)
        return True
    except ValueError:
        return False
