import time
import requests
import streamlit as st

from my_logger import log_error


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    def wait_before_next_request() -> None:
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        my_bar = st.progress(0, text="Waiting before next request...")
        for percent_complete in range(10):
            time.sleep(0.7)
            my_bar.progress((percent_complete+1)*10, text="Waiting before next request...")
        time.sleep(1)
        my_bar.empty()

    try_counter = 0
    ph_xml_import = st.empty()
    while True:
        try_counter += 1
        try:
            response = requests.get(f'https://boardgamegeek.com/xmlapi2/{link}', timeout=10)
        except requests.exceptions.HTTPError as error:
            log_error(f'import_xml_from_bgg - Http error: {error}. Link: {link}')
            raise ValueError("BGG website http error")
        except requests.exceptions.ConnectionError as error:
            log_error(f'import_xml_from_bgg - Error connecting: {error}. Link: {link}')
            raise ValueError("BGG website error connecting")
        except requests.exceptions.Timeout as error:
            log_error(f'import_xml_from_bgg - Timeout error: {error}. Link: {link}')
            raise ValueError("BGG website timeout error")
        except Exception as error:
            log_error(f'import_xml_from_bgg - General exception: {error}. Link: {link}')
            raise ValueError("BGG website error")

        match response.status_code:
            case 200:
                # successful request
                break
            case 202:
                if try_counter == 1:
                    ph_xml_import.caption(f'Request {try_counter}: BGG is preparing dataset')
                else:
                    ph_xml_import.caption(f'Request {try_counter}: BGG is not ready yet')
            case 429:
                ph_xml_import.caption(f'Request {try_counter}: BGG is busy to answer...')
            case 503:
                ph_xml_import.caption(f'Request {try_counter}: BGG is unavailable...')
            case _:
                ph_xml_import.caption(response.status_code)

        wait_before_next_request()

        ph_xml_import.empty()
        if try_counter > 20:
            raise ValueError("Too many trials")

    text = response.content.decode(encoding="utf-8")
    return text
