import requests 
from .global_variables import TELEGRAM_BOT_NAME,BOT_TOKEN


def send_telegram_message(chat_ids=[662144469],messages=[]):
    url = 'https://api.telegram.org/bot'+BOT_TOKEN+'/sendMessage' 
    if messages:
        for message in messages:
            for chat_id in chat_ids:
                payload = {'chat_id' : chat_id,'text' : message}
                requests.post(url,json=payload)
    return True


