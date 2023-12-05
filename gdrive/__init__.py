import io
from datetime import datetime, timedelta

import googleapiclient.discovery
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

import logging
import my_logger

logging.basicConfig(level=logging.INFO)
logger, syslog = my_logger.getlogger(__name__)
logger.propagate = False
logger.setLevel(logging.INFO)


@st.cache_data
def authenticate() -> googleapiclient.discovery.Resource:
    scopes = ['https://www.googleapis.com/auth/drive']
    service_account_info = {
        "type": "service_account",
        "project_id": "simple-bgg-stat-service-acc",
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/simple-bgg-stat-sa%40simple-bgg-stat-service-acc.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
    service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    return service


def create_folder(service: googleapiclient.discovery.Resource, parent_folder: str, folder_name: str) -> str:
    file_metadata2 = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder]
    }
    file = service.files().create(body=file_metadata2, fields="id").execute()
    folder_id = file.get("id")
    return folder_id


def save_new_file(service: googleapiclient.discovery.Resource,
                  parent_folder: str, file_name: str, df: pd.DataFrame) -> str:
    file_metadata = {
        'name': file_name,
        'parents': [parent_folder],
        'mimeType': 'text / csv'
    }
    buffer = io.BytesIO()
    df.to_csv(buffer, sep=",", index=False, encoding="UTF-8")
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='text / csv')
    file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
    file_id = file.get("id")
    return file_id


def delete_file(service: googleapiclient.discovery.Resource, file_id: str) -> None:
    service.files().delete(fileId=file_id).execute()
    return None


def search(service: googleapiclient.discovery.Resource, query: str):
    results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
    return results.get('files', [])


def save(service: googleapiclient.discovery.Resource, parent_folder: str,
         filename: str, df: pd.DataFrame, concat: bool) -> str:
    def create_token() -> str:
        # create token
        token = str(datetime.now())
        df_session = pd.DataFrame(["test"])
        session_folder_id = st.secrets["gdrive_session"]
        token_id = save_new_file(service, parent_folder=session_folder_id, file_name=token, df=df_session)

        # delete old broken tokens
        file = service.files().get(fileId=token_id, fields='modifiedTime').execute()
        token_saving_time = datetime.strptime(file.get('modifiedTime'), "%Y-%m-%dT%H:%M:%S.%fZ")
        items = search(service, query=f'"{session_folder_id}" in parents')
        if items:
            for item in items:
                if item["id"] == token_id:
                    continue
                else:
                    item_time = datetime.strptime(item["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    if token_saving_time-item_time > timedelta(seconds=15):
                        delete_file(service, item["id"])
                        logger.info(f'Found an old token!')

        # waits until this is the first token in time (wait till other threads finish)
        while 0 == 0:
            items = search(service, query=f'"{session_folder_id}" in parents')
            if not items:
                continue
            first_token_id = items[0]["id"]
            first_token_time = items[0]["modifiedTime"]
            for item in items:
                if first_token_time > item["modifiedTime"]:
                    first_token_id = item["id"]
                    first_token_time = item["modifiedTime"]
            if first_token_id == token_id:
                break
        # ready to go
        return token_id

    def delete_token(token: str) -> None:
        delete_file(service, token)

    q = (f'"{parent_folder}" in parents and name contains "{filename}"')
    items = search(service, q)
    if not items:
        # create new file
        file_id = save_new_file(service, parent_folder, filename, df)
        logger.info(f'File saved: {filename}')
    else:
        # overwrite existing file
        existing_file_id = items[0]["id"]
        my_token = create_token()
        if concat:
            df_existing = load(service, items[0]["id"])
            df_merged = pd.concat([df_existing, df], ignore_index=True)
            df_merged = df_merged.drop_duplicates()
        else:
            df_merged = df
        delete_file(service, existing_file_id)
        file_id = save_new_file(service, parent_folder, filename, df_merged)
        delete_token(my_token)
        logger.info(f'File overwritten: {filename}')
    return file_id


def load(service, file_name: str) -> pd.DataFrame:
    try:
        request = service.files().get_media(fileId=file_name)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
    except HttpError as error:
        logger.error(f'While loading file, an error occurred: {error}')
        file = None
    source = io.StringIO(file.getvalue().decode(encoding='utf-8', errors='ignore'))
    df = pd.read_csv(source)
    return df
