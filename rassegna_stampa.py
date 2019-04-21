#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random
import datetime as dt
from lxml import html
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import urllib.parse
import json

URL = 'http://www.giornalone.it/quotidiani_italiani/'
base_url = 'http://www.giornalone.it'
headers = {'User-Agent':\
	'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}

giornali = {\
'Libero': '/prima_pagina_libero',\
'La verità': '/prima_pagina_la_verita/',\
'Il giornale': '/prima_pagina_il_giornale/',\
'Il tempo': '/prima_pagina_il_tempo/',\
'Il fatto quotidiano': '/prima_pagina_il_fatto_quotidiano/',\
'La repubblica': '/prima_pagina_la_repubblica/',\
'Il messaggero': '/prima_pagina_il_messaggero/',\
'Il mattino': '/prima_pagina_il_mattino/',\
'Il gazzettino': '/prima_pagina_il_gazzettino/',\
'La stampa': '/prima_pagina_la_stampa/',\
'Il manifesto': '/prima_pagina_il_manifesto/',\
'Il secolo XIX': '/prima_pagina_il_secolo_xix/',\
'La gazzetta del mezzogiorno': '/prima_pagina_la_gazzetta_del_mezzogiorno/',\
'Il resto del carlino': '/prima_pagina_il_resto_del_carlino/',\
'L\'unione sarda': '/prima_pagina_l_unione_sarda/',\
'Avvenire': '/prima_pagina_avvenire/',\
'L\'Osservatore romano': '/prima_pagina_l_osservatore_romano/',\
'Il dubbio': '/prima_pagina_il_dubbio/',\
'La notizia': '/prima_pagina_la_notizia/'\
}

TOKEN = 'IL TOKEN'
API_URL = 'https://api.telegram.org/bot%s' % (TOKEN)
id_canale = 666
id_mio = 666
canali_rassegna = set([])
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
		response_google_translate = requests_retry_session().\
				get('https://translate.google.com/translate?sl=en&\
tl=it&js=y&prev=_t&hl=it&ie=UTF-8&u=%s&edit-text=&\
act=url' % (url), headers=headers)
		if response_google_translate.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN GOOGLE TRANSLATE\
					PRIMA PASSATA')
		xpath_google_translate = html.fromstring(\
				response_google_translate.content)
		url_reale = xpath_google_translate.\
				xpath('//div[@id="contentframe"]//iframe/@src')[0]
		response_google_translate =\
				requests_retry_session().get(url_reale, headers=headers)
		if response_google_translate.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN GOOGLE TRANSLATE\
					SECONDA PASSATA')
		html_google= response_google_translate.content
		xpath_google_translate = html.fromstring(html_google)
		return xpath_google_translate.xpath('//a/@href')[0]
	
	return url # proxy == None

def my_json_serialize(l):
	big_string = '['
	for x in l:
		big_string += '{"type": "photo", "media": "%s"},' % (x)
	big_string = big_string[:-1] + ']'
	return urllib.parse.quote(big_string)

def get_updates(current_time):
	req_url = "{}/getUpdates".format(API_URL)
	updates = json.loads(requests_retry_session().get(req_url).text)
	updates = updates["result"]
	for i, update in enumerate(updates):
		message = update["message"]
		if "entities" not in message:
			del updates[i]
			continue
		
		dont_delete = False
		for entity in message["entities"]:
			if entity["type"] == "bot_command":
				dont_delete = True
				break
		if not dont_delete:
			del updates[i]
			continue
	return updates

def send_message(chat_id, text, markdown=False):
	req_url = '%s/sendMessage?chat_id=%s&text=%s'\
			% (API_URL, chat_id, text)
	if markdown:
		req_url += '&parse_mode=Markdown'
	response_message = requests_retry_session().get(req_url)

def send_photo_url(chat_id, url_photo):
	req_url = '%s/sendPhoto?chat_id=%s&photo=%s'\
			% (API_URL, chat_id, url_photo)
	response_message = requests_retry_session().get(req_url)

def send_media_group(chat_id, media_group):
	req_url = '%s/sendMediaGroup?chat_id=%s&media=%s'\
			% (API_URL, chat_id, media_group)
	response_message = requests_retry_session().get(req_url)

def send_rassegna(chat_id, img_list, old_list):
	send_message(chat_id, '*== RASSEGNA GIORNO %s ==*'\
			% str(dt.date.today()), True)
	
	# feature non voluta
	# for old in old_list:
		# send_message(chat_id,\
			# '\"%s\" ha un\'edizione vecchia e quindi non lo visualizzo'\
			# % old)
	
	for i in range(0, len(img_list), 10):
		send_media_group(chat_id, my_json_serialize(img_list[i:i+10]))

def scarica_rassegna(id_chat, test=False, proxy=None):
	if test:
		id_chat = [id_mio]
	
	img_list = []
	old_list = []
	
	for name_pp, url_pp in giornali.items():
		url_giornale = base_url + url_pp
		giornale_response = requests_retry_session().get(\
				get_proxy_url(url_giornale, proxy=proxy), headers=headers)
		if giornale_response.status_code == 403:
			send_message(id_mio, '403 FORBIDDEN DI %s' %(url_giornale))
			continue
		giornale_content = html.fromstring(giornale_response.content)
		giornale_content = giornale_content.xpath('//div[@id="left"]')[0];
		if len(giornale_content.\
				xpath('//div[contains(@class, "edition-bar-old")]')) > 0:
			# il giornale e' vecchio
			old_list.append(name_pp)
			continue
		url_img = base_url +giornale_content.\
				xpath('//div[@id="giornale-wrap"]/img/@src')[0]
		ls = url_img.rfind("/") # last_slash
		url_img = url_img[:ls+1] + "." + url_img[ls:]
		img_list.append(url_img)
		time.sleep(5)
	
	for chat in id_chat:
		send_rassegna(chat, img_list, old_list)

def main():
	rassegna_fatta = False
	orario_rassegna = 8
	orario_rassegna -= 2 # differenza di orario, da modificare quando
	# scatta l'ora legale/solare (non ho voglia di fare di meglio)
	delta = 30
	while True:
		now = dt.datetime.utcnow()
		epoch_now = time.time()
		if now.hour == orario_rassegna and not rassegna_fatta:
			scarica_rassegna(id_chat=canali_rassegna, test=False,\
proxy=GOOGLE_TRANSLATE)
			rassegna_fatta = True
		if now.hour != orario_rassegna and rassegna_fatta:
			rassegna_fatta = False
		updates = get_updates(epoch_now)
		for update in updates:
			message = update["message"]
			if abs(epoch_now - message["date"]) <= delta:
				if message["text"].startswith("/rassegna"):
					send_message(message["chat"]["id"], "Mo arrivo zzi'")
					scarica_rassegna(id_chat=[message["chat"]["id"]],\
test=False, proxy=GOOGLE_TRANSLATE)
				elif message["text"].startswith("/aggiungi_questo_canale"):
					canali_rassegna.add(message["chat"]["id"])
					send_message(message["chat"]["id"], "Canale aggiunto.")
				elif message["text"].startswith("/rimuovi_questo_canale"):
					canali_rassegna.discard(message["chat"]["id"])
					send_message(message["chat"]["id"], "Canale rimosso.")
		print("Lista canali: {}".format(canali_rassegna))
		time.sleep(delta)

def test():
	scarica_rassegna(test=True, proxy=GOOGLE_TRANSLATE)

if __name__ == '__main__':
	# scarica_rassegna(test=False, proxy=GOOGLE_TRANSLATE, id_chat=[id_canale])
	main()
