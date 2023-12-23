from my_gdrive import authenticate
from my_gdrive.constants import replace_names
from my_logger import logger


def search(query: str):
    service = authenticate()
    updated_query = replace_names(query)
    try:
        results = service.files().list(q=updated_query, fields="files(id, name, modifiedTime)").execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f'Search error: {e}')
        return None


def search_native(query: str):
    service = authenticate()
    try:
        results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f'Search error: {e}')
        return None
