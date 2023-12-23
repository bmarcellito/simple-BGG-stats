import time
import requests

from my_logger import logger


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    while True:
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
        if response.status_code == 200:
            break
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        time.sleep(5)
    return response.content.decode(encoding="utf-8")
