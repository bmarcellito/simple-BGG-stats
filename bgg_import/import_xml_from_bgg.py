import time
import requests
import streamlit as st

from my_logger import logger


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    try_counter = 0
    ph_xml_import = st.empty()
    while True:
        try_counter += 1
        ph_xml_import.empty()
        try:
            response = requests.get(f'https://boardgamegeek.com/xmlapi2/{link}', timeout=10)
        except requests.exceptions.HTTPError as err:
            logger.error(f'Http error: {err}. Link: {link}')
            continue
        except requests.exceptions.ConnectionError as err:
            logger.error(f'Error connecting: {err}. Link: {link}')
            continue
        except requests.exceptions.Timeout as err:
            logger.error(f'Timeout error: {err}. Link: {link}')
            continue
        except requests.exceptions.RequestException as err:
            logger.error(f'Other request error: {err}. Link: {link}')
            continue
        match response.status_code:
            case 200:
                break
            case 202:
                if try_counter == 1:
                    ph_xml_import.caption(f'Request {try_counter}: BGG is preparing dataset')
                else:
                    ph_xml_import.caption(f'Request {try_counter}: BGG is not ready yet')
            case 429:
                ph_xml_import.caption(f'Request {try_counter}: BGG is busy to answer...')
            case _:
                print(response.status_code)
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        my_bar = st.progress(0, text="Waiting before next request...")
        for percent_complete in range(10):
            time.sleep(0.7)
            my_bar.progress((percent_complete+1)*10, text="Waiting before next request...")
        time.sleep(1)
        my_bar.empty()
        # time.sleep(8)
    ph_xml_import.empty()
    return response.content.decode(encoding="utf-8")
