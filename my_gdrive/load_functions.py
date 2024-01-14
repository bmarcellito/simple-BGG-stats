import io
import pandas as pd
from googleapiclient.http import MediaIoBaseDownload

from my_gdrive import authenticate
from my_logger import log_error


def load(file_id: str) -> io.BytesIO:
    try:
        service = authenticate()
    except ValueError:
        raise ValueError("Failed to load file")

    try:
        request = service.files().get_media(fileId=file_id)
    except Exception as error:
        log_error(f'load - While loading file, an error occurred: {type(error)}')
        raise ValueError("Failed to load file")

    file = io.BytesIO()
    try:
        downloader = MediaIoBaseDownload(file, request)
    except Exception as error:
        log_error(f'load - While loading file, an error occurred: {type(error)}')
        raise ValueError("Failed to load file")

    done = False
    while done is False:
        try:
            status, done = downloader.next_chunk()
        except Exception as error:
            log_error(f'load - While loading file, an error occurred: {type(error)}')
            raise ValueError("Failed to load file")
    return file


def load_zip(file_id: str) -> pd.DataFrame:
    try:
        file = load(file_id)
    except ValueError:
        raise ValueError("Failed to load file")
    source = io.BytesIO(file.getvalue())
    df = pd.read_csv(source, compression={'method': 'zip'})
    return df


def load_csv(file_id: str) -> pd.DataFrame:
    try:
        file = load(file_id)
    except ValueError:
        raise ValueError("Failed to load file")
    source = io.StringIO(file.getvalue().decode(encoding='utf-8', errors='ignore'))
    df = pd.read_csv(source)
    return df
