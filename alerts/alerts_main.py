from time import sleep
from datetime import datetime,timedelta,date,time
from pymongo import MongoClient
import pandas as pd
from apscheduler.scheduler import Scheduler
import numpy as np
import requests
from stockstats import StockDataFrame as Sdf
import json
import os

# all the essential functions
from essentials.bot import send_telegram_message
from essentials.global_variables import mongo_connection_string
from essentials.custom_indicators import SuperTrend
from essentials.alert_dict import Alerts
from eod_updater import updateHistoricalData
from helper import *
from dbhelper import get_candles,get_alerts

'''
purpose of this file?

this is the main file (heart of the product) all the calculation and crons are handeled from here
scheduling of cron is also done here

'''



# scheduler used to run the function every 15 mins
sched = Scheduler()
sched.start()

# array of custom indicators not available in stockstats
custom_indicators = ['ST']


# web node(root) automatically sleeps after 30 mins of inactivity
# this fuction is used with a 25 mins cron that wont let node sleep while fetching live data
# as it checks if market is open it 'll allow to sleep after 3:30  
def wakeup_node():
    if check_if_market_open():
        # make get request to root url
        URL = "https://birdwatchers.herokuapp.com/"
        r = requests.get(url = URL)
        print('wakeup node call')
    else:
        print(' market closed no wakeup call needed')



def evaluateAlertConditions(alert_conditions,data):
    alert_eligible = False
    for alert_condition in alert_conditions:
        # check for line crossovers
        if 'line_crossover' in list(alert_condition.keys()):
            print('calculating line_crossover')
            # get crossover details
            line_crossover = alert_condition['line_crossover']
            first_line = line_crossover[0]
            second_line = line_crossover[1]
            cross_type = line_crossover[2]
            # get crossover values
            data['crossover'] = data[first_line] - data[second_line]
            
            # if crossover happened (check last 2 rows)
            if np.sign(data['crossover'][-1]) != np.sign(data['crossover'][-2]):
                # send alert
                if np.sign(data['crossover'][-1]) == 1 and cross_type == 'up':
                    alert_eligible = True
                elif np.sign(data['crossover'][-1]) == -1 and cross_type == 'down':
                    alert_eligible = True
                elif cross_type == 'any':
                    alert_eligible = True
                else:
                    alert_eligible = False
                    break
            else:
                alert_eligible = False
                break
        # /line crossover

        # check for value crossovers
        if 'value_crossover' in list(alert_condition.keys()):
            print('calculating value_crossover')
            # get crossover details
            value_crossover = alert_condition['value_crossover']
            # get line
            line = value_crossover[0]
            # get values for alerts
            # temp hack to resolve the error without making major changes (28 july)
            cross_type = value_crossover[2]
            upper_value = None
            lower_value = None
            if cross_type == 'up':
                upper_value = float(value_crossover[1])
            elif cross_type == 'down':
                lower_value = float(value_crossover[1])
            elif cross_type == 'any':
                lower_value = float(value_crossover[1])
                upper_value = float(value_crossover[1])
            # /temp hack
            # upper_value = value_crossover[1]
            # lower_value = value_crossover[2]
            # cross_type = value_crossover[3]
            # get line current and previous value
            latest_val = data[line][-1]
            previous_val = data[line][-2]
            # if alert on upper value set
            if upper_value:
                # check if it actually crossed and was not already up
                if (latest_val > upper_value) and (previous_val < upper_value) and (cross_type == 'up'):
                    alert_eligible = True
            # if alert on lower value set
            if lower_value:
                # check if it actually crossed and was not already low
                if (latest_val < lower_value )and (previous_val > lower_value) and (cross_type == 'down'):
                    alert_eligible = True
            
            if alert_eligible == False:
                break
        # /value crossover

        # above line condition
        if 'above_line' in list(alert_condition.keys()):
            above_line = alert_condition['above_line']
            line1 = above_line[0]
            line2 = above_line[1]
            # check if line1 is above line2 
            diff = data[line1][-1] - data[line2][-1]
            if np.sign(diff) == 1:
                alert_eligible = True
            else:
                alert_eligible = False
                break
        # /above line condition

        # below line condition
        if 'below_line' in list(alert_condition.keys()):
            below_line = alert_condition['below_line']
            line1 = below_line[0]
            line2 = below_line[1]
            # check if line1 is above line2 
            diff = data[line1][-1] - data[line2][-1]
            if np.sign(diff) == -1:
                alert_eligible = True
            else:
                alert_eligible = False
                break
        # /below line condition

        # above value condition
        if 'above_value' in list(alert_condition.keys()):
            above_value = alert_condition['above_value']
            line1 = above_value[0]
            value_to_check = above_value[1]
            if RepresentsInt(value_to_check):
                value_to_check = float(value_to_check)
            else:
                continue
            # check if line1 is above value_to_check 
            diff = data[line1][-1] - value_to_check
            if np.sign(diff) == 1:
                alert_eligible = True
            else:
                alert_eligible = False
                break
        # /above value condition

        # below value condition
        if 'below_value' in list(alert_condition.keys()):
            below_value = alert_condition['below_value']
            line1 = below_value[0]
            value_to_check = below_value[1]
            if RepresentsInt(value_to_check):
                value_to_check = float(value_to_check)
            else:
                continue
            # check if line1 is above value_to_check 
            diff = data[line1][-1] - value_to_check
            if np.sign(diff) == -1:
                alert_eligible = True
            else:
                alert_eligible = False
                break
        # /below value condition
    return alert_eligible


# this same function can be used for all the Alerts by jsut passing arg '5mins','15mins'
def calcAlerts(candle):
    # if no alerts present for this candle
    if candle not in get_candles():
        return False
    # get all candle alters
    candle_alerts = get_alerts(candle)
    # make mongo connection
    client = MongoClient(mongo_connection_string)
    # for every elerts
    for alert in candle_alerts:
        # get indicator needed
        indicators_needed = alert['indicators']
        print('executing for '+str(indicators_needed))
        alert_conditions = alert['alert_conditions']
        ''' note : fix this part cz data for same ticker is fetched multiple times maybe save it to a pickle? and reduce the complexity '''
        watchlist = alert['watchlist']
        for stock in watchlist:
            print('getting '+stock)
            ''' this 'll be replaced by zerodha historical'''
            df2 = checkIfFetched(stock,candle)
            if len(df2) == 0:
                print('data not saved')
                # get historical data
                # get database object
                db = client.Historical_Data
                collection = db[stock]
                # get all the rows
                df = pd.DataFrame(list(collection.find().sort([('timestamp', -1)]).limit(3000)))
                df.sort_values(by='timestamp', ascending=True,inplace=True)
                # df = pd.DataFrame(list(collection.find())
                print('got historical')
                # df = pd.DataFrame(list(collection.find().sort([('timestamp', -1)]).limit(100)))
                # df.sort_values(['timestamp'], ascending=[True],inplace=True)
                df.set_index('timestamp',inplace=True)
                loffset = None
                # to handle candles greater than 15 mins  we use loffset in resample
                mins = getNumTillChar(candle)
                if mins >15:
                    loffset = str(mins-15)+'min'
                if loffset is None:
                    df2 = df.resample(candle).agg({'open': 'first','high':'max','low':'min', 'close': 'last','volume':'sum'})
                else:
                    df2 = df.resample(candle, loffset=loffset).agg({'open': 'first','high':'max','low':'min', 'close': 'last','volume':'sum'})
                df2.dropna(inplace=True)
                '''todo-----'''
                # get live data
                db = client.Zerodha_LiveData
                collection = db[stock]
                # round minute part 'll be changed depending on the candle
                query = {
                    "timestamp": {
                        "$gte":datetime.combine(date.today(),time(9,15)),
                        "$lt":round_candle(datetime.now(), 'down', getNumTillChar(candle)).replace(microsecond=0, second=0)
                    }
                }
                live_data =  pd.DataFrame(list(collection.find(query)))
                # if no live data fetched some issue with the requested candle
                print('got live data')
                if len(live_data) == 0:
                    print('no live data present for this candle')
                    continue
                live_data.set_index('timestamp',inplace=True)
                # to handle candles greater than 15 mins  we use loffset in resample
                if loffset is None:
                    ohlc = live_data['last_price'].resample(candle).ohlc()
                    # ohlc['volume'] = live_data['volume'].resample(candle).sum()
                    ohlc['volume_f'] = live_data['volume'].resample(candle).first()
                    ohlc['volume_l'] = live_data['volume'].resample(candle).last()
                    ohlc['volume'] = ohlc['volume_l'] - ohlc['volume_f']
                    ohlc.drop(columns=['volume_f', 'volume_l'],inplace=True)
                else:
                    ohlc = live_data['last_price'].resample(candle,loffset=loffset).ohlc()
                    # ohlc['volume'] = live_data['volume'].resample(candle,loffset=loffset).sum()
                    ohlc['volume_f'] = live_data['volume'].resample(candle,loffset=loffset).first()
                    ohlc['volume_l'] = live_data['volume'].resample(candle,loffset=loffset).last()
                    ohlc['volume'] = ohlc['volume_l'] - ohlc['volume_f']
                    ohlc.drop(columns=['volume_f', 'volume_l'],inplace=True)
                # resample live data and concat it with historical data
                ''' concat livedata here + ignore incomplete candle and dropna'''
                df2 = df2.append(ohlc)
                df2.dropna(inplace=True)
                print('concated hist & live')
                # save pkl file 
                df2.to_pickle(getFilenamePKL(stock,candle))
                print('saved to pkl')
            # calculate indicators
            data = df2.copy()
            for ind in indicators_needed:
                print('calculating indicators')
                # check if indicator starts with any of the customindicator
                if list(filter(ind['line_name'].startswith, custom_indicators)) != []:
                    # check if suppertrend
                    if ind['line_name'].startswith('ST'):
                        # get variables needed
                        _,period , multiplier = ind['line_name'].split('_')
                        # calculate supertrend
                        data = SuperTrend(data,int(period),int(multiplier),ohlc=['open', 'high', 'low', 'close'])
                    # other self calculated indicators code goes here
                else:
                    if "values" in list(ind.keys()):
                        for k,v in ind["values"].items():
                            setattr(Sdf, k, v)
                    # if indicator already available in stockstat
                    stock_df = Sdf.retype(data)
                    data[ind['line_name']] = stock_df[ind['line_name']]
            
            alert_eligible = evaluateAlertConditions(alert_conditions,data)
            # /alert conditions loop
            if alert_eligible:
                tele_msg = alert['message'].format(stock = stock, candle = candle)
                send_telegram_message(chat_ids=alert['tele_id'],messages=[tele_msg])

        # /stock loop
    # /alert loop
    client.close()
    # when the candel data/alerts for that candle is made we no longer need tempstorage pkls
    print('clear temp storage')
    clearTempStorage()
    return True


# wakeup node cron
print('scheduling wakeup_node')
sched.add_interval_job(wakeup_node, minutes=20)

# schedule data update part
# print('scheduling update historical')
# sched.add_cron_job(updateHistoricalData, day_of_week='mon-fri', hour=19,minute=51)
# sched.add_cron_job(updateHistoricalData, day_of_week='mon-fri', hour=18,minute=5)


def AlertCronHandler():
    if check_if_market_open():
        print('market open executing candles')
        # read json file 
        with open('candle_execution_log.json', 'r') as f:
            data = json.loads(f.read())
        if len(data):
            # get data for 5min,15min,..
            for candle,last_exec in data.items():
                # compare if last execution < time it should execute
                if datetime.strptime(last_exec, '%Y-%m-%d %H:%M:%S.%f') < round_candle(datetime.now(), 'down', getNumTillChar(candle)):
                    # execute it for that specific time 
                    print('execution neede for '+candle)
                    calcAlerts(candle)
                    # update the json
                    data[candle] = str(datetime.now())
                    print('updated data log')
                    with open('candle_execution_log.json', 'w') as f:
                        json.dump(data, f)
                else:
                    print('probably already executed '+candle)
            # for new strategies added 
            new_candels = list(set(get_candles()).difference(set(data.keys())))
            for candle in new_candels:
                calcAlerts(candle)
                data[candle] = str(datetime.now())
                print('updated data log for newly added candle '+candle)
                with open('candle_execution_log.json', 'w') as f:
                    json.dump(data, f)
        # if no logs created yet
        elif len(Alerts):
            data = {}
            for candle in list(get_candles()):
                calcAlerts(candle)
                data[candle] = str(datetime.now())
            print('craeted new log for all candle')
            with open('candle_execution_log.json', 'w') as f:
                json.dump(data, f)


# schedule cron for candels
sched.add_interval_job(AlertCronHandler, seconds=45)
# sched.add_interval_job(AlertCronHandler, minutes=1)

# keep on running untill all candels are made
while sched.running:
    sleep(1)






