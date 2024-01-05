import io
import pandas as pd
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from my_gdrive import authenticate
from my_logger import log_error


def load(file_id: str) -> io.BytesIO:
    service = authenticate()
    try:
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            try:
                status, done = downloader.next_chunk()
            except Exception as error:
                log_error(f'load - While loading file, an error occurred: {error}')
    except HttpError as error:
        log_error(f'load - While loading file, an error occurred: {error}')
        file = None
    return file


def load_zip(file_id: str) -> pd.DataFrame:
    file = load(file_id)
    source = io.BytesIO(file.getvalue())
    df = pd.read_csv(source, compression={'method': 'zip'})
    return df


def load_csv(file_id: str) -> pd.DataFrame:
    file = load(file_id)
    source = io.StringIO(file.getvalue().decode(encoding='utf-8', errors='ignore'))
    df = pd.read_csv(source)
    return df
