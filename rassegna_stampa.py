#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random
import datetime
from lxml import html
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

URL = 'http://www.giornalone.it/quotidiani_italiani/'
base_url = 'http://www.giornalone.it'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
ci_devono_essere = ['/prima_pagina_libero/', '/prima_pagina_la_verita/', '/prima_pagina_il_giornale/', '/prima_pagina_il_tempo/']
nomi_giornali = ['Libero', 'La verità', 'Il giornale', 'Il tempo']
url_prime_pagine_caso = ['/prima_pagina_il_fatto_quotidiano/', '/prima_pagina_la_repubblica/', '/prima_pagina_il_messaggero/', '/prima_pagina_il_mattino/', '/prima_pagina_il_gazzettino/', '/prima_pagina_la_stampa/', '/prima_pagina_il_manifesto/', '/prima_pagina_il_secolo_xix/', '/prima_pagina_la_gazzetta_del_mezzogiorno/', '/prima_pagina_il_resto_del_carlino/', '/prima_pagina_l_unione_sarda/', '/prima_pagina_avvenire/', '/prima_pagina_l_osservatore_romano/']
TOKEN = 'il_token'
API_URL = 'https://api.telegram.org/bot%s' % (TOKEN)
id_canale = ID_DEL_CANALE
id_mio = ID_MIO_PER_I_TEST
GOOGLE_TRANSLATE = 1


def requests_retry_session(
		retries=3,
		backoff_factor=0.3,
		status_forcelist=(500, 502, 504),
		session=None,
		):
	session = session or requests.Session()
	retry = Retry(
		total=retries,
		read=retries,
		connect=retries,
		backoff_factor=backoff_factor,
		status_forcelist=status_forcelist,
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount('http://', adapter)
	session.mount('https://', adapter)
	return session

GLOBXPATH=None
def get_proxy_url(url, proxy=None):
	if proxy == GOOGLE_TRANSLATE:
		response_google_translate = requests_retry_session().get('https://translate.google.com/translate?sl=en&tl=it&js=y&prev=_t&hl=it&ie=UTF-8&u=%s&edit-text=&act=url' % (url), headers=headers)
		if response_google_translate.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN GOOGLE TRANSLATE PRIMA PASSATA')
		xpath_google_translate = html.fromstring(response_google_translate.content)
		url_reale = xpath_google_translate.xpath('//div[@id="contentframe"]//iframe/@src')[0]
		response_google_translate = requests_retry_session().get(url_reale, headers=headers)
		if response_google_translate.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN GOOGLE TRANSLATE SECONDA PASSATA')
		html_google= response_google_translate.content
		xpath_google_translate = html.fromstring(html_google)
		return xpath_google_translate.xpath('//a/@href')[0]
	
	return url # proxy == None

def send_message(chat_id, text):
	response_message = requests_retry_session().get('%s/sendMessage?chat_id=%s&text=%s' % (API_URL, chat_id, text))

def send_photo_url(chat_id, url_photo):
	response_message = requests_retry_session().get('%s/sendPhoto?chat_id=%s&photo=%s' % (API_URL, chat_id, url_photo))

def scarica_rassegna(test=False, proxy=None):
	id_chat = id_canale
	if test:
		id_chat = id_mio
	
	url_prime_pagine = ci_devono_essere
	for url_pp in url_prime_pagine:
		url_giornale = base_url + url_pp
		giornale_response = requests_retry_session().get(get_proxy_url(url_giornale, proxy=proxy), headers=headers)
		if giornale_response.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN DI %s' %(url_giornale))
		giornale_content = html.fromstring(giornale_response.content)
		giornale_content = giornale_content.xpath('//div[@id="left"]')[0];
		if len(giornale_content.xpath('//div[contains(@class, "edition-bar-old")]')) > 0:
			# il giornale e' vecchio
			nome_giornale = nomi_giornali[url_prime_pagine.index(url_pp)]
			send_message(id_chat, '"%s" c\'ha un\'edizione vecchia e quindi non lo visualizzo.' % (nome_giornale))
			continue
		url_img = base_url + giornale_content.xpath('//div[@id="giornale-wrap"]/img/@src')[0]
		send_photo_url(id_chat, url_img)
		time.sleep(5)
	
	while True:
		if len(url_prime_pagine_caso) == 0:
			send_message(id_chat, 'Nessuna pagina random con edizione nuova')
			break
		url_pagina_random = random.choice(url_prime_pagine_caso)
		url_prime_pagine_caso.remove(url_pagina_random)
		url_giornale = base_url + url_pagina_random
		giornale_response = requests_retry_session().get(get_proxy_url(url_giornale, proxy=proxy), headers=headers)
		if giornale_response.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN DI PAGINA RANDOM %s' %(url_giornale))
		giornale_content = html.fromstring(giornale_response.content)
		giornale_content = giornale_content.xpath('//div[@id="left"]')[0];
		if len(giornale_content.xpath('//div[contains(@class, "edition-bar-old")]')) > 0:
			# il giornale e' vecchio
			continue
		url_img = base_url + giornale_content.xpath('//div[@id="giornale-wrap"]/img/@src')[0]
		send_photo_url(id_chat, url_img)
		break

def main():
	orario_pubblicazione = datetime.time(7, 0, 0)
	print('Orario pubblicazione: %02d:%02d:%02d' %(orario_pubblicazione.hour, orario_pubblicazione.minute, orario_pubblicazione.second))
	
	dt = datetime.datetime.now()
	hour = dt.hour
	minute = dt.minute
	second = dt.second
	if minute != 0 or second != 0:
		time.sleep(60 - second)
		time.sleep((60 - minute - 1)*60)
		# mo l'orario dovrebbe essere un'ora piena, circa
	
	while True:
		dt = datetime.datetime.now()
		hour = dt.hour
		minute = dt.minute
		second = dt.second
		
		print('TICK: %02d:%02d:%02d' %(hour, minute, second))
		if hour == orario_pubblicazione.hour:
			scarica_rassegna(test=False, proxy=GOOGLE_TRANSLATE)
		time.sleep(3600)

def test():
	scarica_rassegna(test=True, proxy=GOOGLE_TRANSLATE)

if __name__ == '__main__':
	main()
