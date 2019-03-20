from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import random
import datetime
import time


AVITO_URL = 'https://www.avito.ru/saratov/bytovaya_tehnika/dlya_kuhni/holodilniki_i_morozilnye_kamery'
BASE_BOT_URL = 'https://api.telegram.org/bot'
TOKEN = ''
PROXIES_URL = 'https://www.sslproxies.org/'
CHAT_ID = ''


def get_html(url, proxy):
    ua = UserAgent()
    header = {'User-Agent': ua.random}
    response = requests.get(url, headers=header, proxies=proxy, timeout=10)
    return response


# Proxy part

def get_proxies(proxies_resp):
    proxies = []
    soup = BeautifulSoup(proxies_resp.text, 'lxml')
    proxies_table = soup.find(id='proxylisttable')
    for row in proxies_table.tbody.find_all('tr'):
        ip = row.findAll('td')[0].string
        port = row.findAll('td')[1].string
        proxies.append({'https': ':'.join([ip, port])})
    return proxies


def get_proxy(proxies):
    random_proxy = random.randint(0, len(proxies) - 1)
    proxy = proxies[random_proxy]
    return proxy

# AVITO part

def get_fridge_data(avito_response, fridge_base):
    ids = [item['id'] for item in fridge_base]
    soup = BeautifulSoup(avito_response.text, 'lxml')
    div = soup.findAll('div', {'class': 'item_table-wrapper'})
    for item in div:
        title = item.find('div', {'class': 'item_table-header'}).find('h3').find('a')['title'].lower()
        publication_date = item.find('div', {'class': 'js-item-date c-2'})['data-absolute-date'][3:10]
        price = item.find('div', {'class': 'about'}).find('span', {'class': 'price'})['content'],
        link = item.find('div', {'class': 'item_table-header'}).find('h3').find('a')['href']
        id_num = link[-10:]
        if 'холодильник' in title and publication_date == 'Сегодня' and id_num not in ids:
            fridge_base.append({
                'id': id_num,
                'phone': get_phone_number(link),
                'title': title,
                'link': link,
                'price': price,
                'publication_date': publication_date,
                'label': '0'
                })
    return fridge_base


def get_phone_number(link):
    fridge_response = get_html('https://m.avito.ru' + link, proxy)
    soup = BeautifulSoup(fridge_response.text, 'lxml')
    try:
        phone = soup.find('a', {'class': '_2MOUQ'})['href'][4:]
    except TypeError:
        phone = 'None'
    return phone


# telegram part

def get_updates_json(request):
    response = requests.get(request + 'getUpdates')
    return response.json()


def last_update(data):
    results = data['result']
    total_updates = len(results) - 1
    return results[total_updates]


def get_chat_id(update):
    chat_id = update['message']['chat']['id']
    return chat_id


def send_message(chat, fridge_base):
    for item in fridge_base:
        if item['label'] == '0':
            item['label'] = '1'
            text = '{}, {}, {}'.format(item['title'],
                                       item['phone'],
                                       item['price']
                                       )
            params = {'chat_id': chat, 'text': text}
            print (bot_url, params)
            requests.post(bot_url + 'sendMessage', data=params)
    return None


if __name__ == '__main__':

    fridge_base = [{'id': 0, 'label': 1}]
    bot_url = BASE_BOT_URL + TOKEN
    while True:
        proxies = get_proxies(get_html(PROXIES_URL, proxy=None))
        checker = True
        while checker:
            try:
                proxy = get_proxy(proxies)
                fridge_base = get_fridge_data(get_html(AVITO_URL, proxy), fridge_base)
                checker = False
            except:
                print('bad proxy')
        #chat_id = get_chat_id(last_update(get_updates_json(bot_url)))
        send_message(CHAT_ID, fridge_base)
        print('пауза 5 минут')
        time.sleep(5*60)
