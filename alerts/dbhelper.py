import json
import requests 



host = 'https://djangoURL/'

def get_alerts(candle):
    API_ENDPOINT = host+"get_alerts_test/"
    data = {'candle':candle,"teleid":662144469}
    r = requests.post(url = API_ENDPOINT, data = data)
    data = json.loads(r.text )
    return data


def get_candles():
    API_ENDPOINT = host+"get_candles/"
    data = {"teleid":662144469}
    r = requests.post(url = API_ENDPOINT, data = data)
    data = json.loads(r.text )
    return data




