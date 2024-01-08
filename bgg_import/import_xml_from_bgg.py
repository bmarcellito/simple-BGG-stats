import time
import requests
import streamlit as st

from my_logger import log_error


class BggAnswer:
    def __init__(self, status, response, data):
        self.status = status
        self.response = response
        self.data = data


def import_xml_from_bgg(link: str) -> BggAnswer:
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
        except requests.exceptions.HTTPError as err:
            log_error(f'import_xml_from_bgg - Http error: {err}. Link: {link}')
            return BggAnswer(False, f'BGG website http error: {err}', "")
        except requests.exceptions.ConnectionError as err:
            log_error(f'import_xml_from_bgg - Error connecting: {err}. Link: {link}')
            return BggAnswer(False, f'BGG website error connecting: {err}', "")
        except requests.exceptions.Timeout as err:
            log_error(f'import_xml_from_bgg - Timeout error: {err}. Link: {link}')
            return BggAnswer(False, f'BGG website timeout error: {err}', "")
        except requests.exceptions.RequestException as err:
            log_error(f'import_xml_from_bgg - Other request error: {err}. Link: {link}')
            return BggAnswer(False, f'BGG website request error: {err}', "")
        except Exception as err:
            log_error(f'import_xml_from_bgg - General exception: {err}. Link: {link}')
            return BggAnswer(False, f'BGG website error: {err}', "")

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
            return BggAnswer(False, "Too many failed trial", "")

    text = response.content.decode(encoding="utf-8")
    result = BggAnswer(True, "", text)
    return result
