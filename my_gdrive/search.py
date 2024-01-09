from my_gdrive import authenticate
from my_gdrive.constants import replace_names
from my_logger import log_error


def search(query: str):
    service = authenticate()
    updated_query = replace_names(query)
    trial = 1
    while True:
        try:
            results = service.files().list(q=updated_query, fields="files(id, name, modifiedTime)").execute()
            return results.get('files', [])
        except Exception as e:
            log_error(f'search - Search error: {e}, trial: {trial}, query: {query}/{updated_query}')
            trial += 1


def search_native(query: str):
    service = authenticate()
    trial = 1
    while True:
        try:
            results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
            return results.get('files', [])
        except Exception as e:
            log_error(f'search_native - Search error: {e}, trial: {trial}, query: {query}')
            trial += 1
