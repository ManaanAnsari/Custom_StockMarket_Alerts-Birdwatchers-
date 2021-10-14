# imort email related stuff
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 
import glob
import os

# import calculation/datascience essentials
from datetime import datetime,timedelta,date,time
from pymongo import MongoClient
import pandas as pd
import numpy as np
from stockstats import StockDataFrame as Sdf

# get essential functions required from other files
from essentials.global_variables import mongo_connection_string
from essentials.custom_indicators import SuperTrend
from essentials.alert_dict import Alerts
from helper import *


'''
purpose of this file?
save report in csvs then email those csvs and then delete it

note: it 'll change after historical purchase

'''


def generate_report():
    return
    client = MongoClient(mongo_connection_string)
    indicators = []
    stock_list = []
    for candle_name,alert_details in Alerts.items():
        for alert in alert_details:
            # print(alert['watchlist'])
            indicators = indicators + alert['indicators']
            stock_list = stock_list + alert['watchlist']
    indicators = list(set(indicators))
    stock_list = list(set(stock_list))
    candles = list(Alerts.keys())

    for candle in candles:
        for stock in stock_list:
            # get historical data
            db = client.Historical_Data
            collection = db[stock]
            query = {
                "timestamp": {
                    "$lt":datetime.combine(date.today(),time(0)),
                }
            }
            df = pd.DataFrame(list(collection.find(query).sort([('timestamp', -1)]).limit(3000)))
            df.sort_values(by='timestamp', ascending=True,inplace=True)
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
            # get live data
            # get live data
            db = client.Zerodha_LiveData
            collection = db[stock]
            # round minute part 'll be changed depending on the candle
            query = {
                "timestamp": {
                    "$gte":datetime.combine(date.today(),time(9,15)),
                    "$lt":datetime.combine(date.today(),time(15,30))
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
            data = df2.copy()
            for ind in indicators:
                print('calculating indicators')
                # check if indicator starts with any of the customindicator
                if list(filter(ind.startswith, custom_indicators)) != []:
                    # check if suppertrend
                    if ind.startswith('ST'):
                        # get variables needed
                        _,period , multiplier = ind.split('_')
                        # calculate supertrend
                        data = SuperTrend(data,int(period),int(multiplier),ohlc=['open', 'high', 'low', 'close'])
                    # other self calculated indicators code goes here
                else:
                    # if indicator already available in stockstat
                    stock_df = Sdf.retype(data)
                    data[ind] = stock_df[ind]
            data = data.loc[datetime.combine(date.today(),time(0)):]
            data.to_csv('./notifier/'+stock+'_'+candle+'.csv')
    send_report()


def send_report():
    files_path = list(glob.glob("./notifier/*.csv"))
    fromaddr = "from@gmail.com"
    password = "shhh!"
    toaddr = "to@gmail.com"
    # instance of MIMEMultipart 
    msg = MIMEMultipart() 
    msg['From'] = fromaddr 
    msg['To'] = toaddr 
    msg['Subject'] = "Report for "+str(date.today())
    body = "Todays report"
    # attach the body with the msg instance 
    msg.attach(MIMEText(body, 'plain')) 
    # creates SMTP session 
    s = smtplib.SMTP('smtp.gmail.com', 587) 
    # start TLS for security 
    s.starttls()
    # Authentication
    try:
        # bird@watchers91
        s.login(fromaddr, password)
    except:
        print('smtp loginerror maybe cz of https://myaccount.google.com/lesssecureapps')
        return False
    for i in range(len(files_path)):
        # open the file to be sent 
        filename = files_path[i].split('/')[-1]
        attachment = open(files_path[i], "rb") 
        # instance of MIMEBase and named as p 
        p = MIMEBase('application', 'octet-stream')         
        # To change the payload into encoded form 
        p.set_payload((attachment).read())         
        # encode into base64 
        encoders.encode_base64(p) 
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)        
        # attach the instance 'p' to instance 'msg' 
        msg.attach(p)
        if i%20 == 0 and i != 0:
            # Converts the Multipart msg into a string 
            text = msg.as_string()
            # sending the mail 
            s.sendmail(fromaddr, toaddr, text)
            # instance of MIMEMultipart 
            msg = MIMEMultipart() 
            msg['From'] = fromaddr 
            msg['To'] = toaddr 
            msg['Subject'] = "Report for "+str(date.today())
            body = "Todays report"
            # attach the body with the msg instance 
            msg.attach(MIMEText(body, 'plain')) 
            print(i,'sending mail')
        if i == len(files_path)-1:
            # Converts the Multipart msg into a string 
            text = msg.as_string()
            # sending the mail 
            s.sendmail(fromaddr, toaddr, text)
            # terminating the session 
            s.quit()
            print(i,'sending last mail')
    clearReportingFiles()


def clearReportingFiles():
    print('removing all pkl file')
    files = glob.glob('./notifier/*.csv')
    for f in files:
        os.remove(f)
    return True

