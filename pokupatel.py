#!/usr/bin/env python

import logging
import time
import re
import os

from splinter import Browser
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import ElementClickInterceptedException


# import os
# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.oauth2.credentials import Credentials

# SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
# DOCUMENT_ID = "19XnW3Fyd422XmFrBEMOV6TusN2R3Ow6QR1N5DcYlyMo"


# if os.path.exists('token.json'):
#     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
# flow = InstalledAppFlow.from_client_secrets_file(
#     f"{os.environ['HOME']}/certs/mirror-mind.json",
#     SCOPES
# )
# creds = flow.run_local_server(port=8080)
# service = build('docs', 'v1')
# document = service.documents().get(documentId=DOCUMENT_ID).execute()
# with open('token.json', 'w') as token:
#     token.write(creds.to_json())




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
log = logging.getLogger(__name__)

COUNT = re.compile(".* (([0-9]+) st) .*")
REA = re.compile("([0-9]+):-")

DICT = {}
for l in open("dict.txt"):
    l = l.strip()
    l_spl = l.split("-")
    
    assert len(l_spl) > 1 and len(l_spl) <= 3
    k = l_spl[0].strip().lower()
    v = l_spl[1].strip().lower()
    if len(l_spl) == 3:
        count = int(l_spl[2])
    else:
        count = 1
    DICT[k] = {"query": v, "count": count}        


def init_browser():
    chrome_service = Service(executable_path='./chromedriver')
    browser = Browser('chrome', service=chrome_service)

    browser.visit('https://www.mathem.se')

    [b for b in browser.find_by_tag("button") if "cookies" in b.text][0].click()
    browser.find_by_text("Logga in").first.click()
    browser.find_by_id("e-mail").fill("alexey.chernushev@gmail.com")
    browser.find_by_id("password").fill(os.environ["MATHEM_PASSWORD"])
    browser.find_by_text("Logga in").first.click()
    return browser


global ctx
def find_an_item(browser, key, count):
    log.info(f"Found {key} from shopping list")
    log.info("Searching in the search bar")
    browser.find_by_id("main-search").fill(key)
    time.sleep(0.5)
    browser.find_by_text("Sök").click()
    time.sleep(0.25)
    browser.find_by_text("Sök").click()
    time.sleep(0.25)
    results = browser.find_by_tag("mathem-product-card")
    log.info(f"Found {len(results)} results")

    panel = None
    for i, r in enumerate(results):
        rea = r.find_by_tag("span").text
        mrea = REA.match(rea)
        if mrea:
            discount = int(mrea.group(1))
            log.info(f"Found a product with a discout {discount}, chosing this as the best")
            panel = r
            break
        elif panel is None:
            fav = r.find_by_css("i.favorite__icon.mh.mh-heart1.favorite__icon--active.ng-star-inserted")
            if fav:
                log.info("Found favorite")
                panel = r
        if i > 5:
            if panel is None:
                raise ValueError(f"Can't find any liked products by this query: {key}")
            break
        
    the_button = None
    ctx = panel
    for i in range(count):
        if the_button is not None:
            the_button.click()
        else:
            buttons = panel.find_by_tag("button")
            if len(buttons) == 4:
                b0, _, b2 = buttons[1:]
            elif len(buttons) == 3:
                b0, _, b2 = buttons
            else:
                raise ValueError(f"Got too many buttons (#{len(buttons)}) on a card for a query {key}")

            try:
                b0.click()
                the_button = b2
            except ElementClickInterceptedException:
                b2.click()
                the_button = b2
        time.sleep(0.2)



browser = init_browser()

for l in open("shopping_list.txt"):
    l = l.strip()
    if not l or l.startswith("Mathem") or l.startswith("#"):
        continue
    if l.startswith("["):
        log.info(f"Section {l}")
        continue
    
    key = l.split("-")[0].lower().strip()
    count = 1
    
    if key in DICT:
        key = DICT[key]["query"]
        count = DICT[key]["count"]
        
    log.info(f"{key} {count}")
    
    find_an_item(browser, key, count)
    
