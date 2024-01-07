import io
from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload

from my_gdrive import authenticate
from my_gdrive.search import search
from my_logger import log_info, log_error
from my_gdrive.constants import get_name


def save_new_csv_file(service: googleapiclient.discovery.Resource, parent_folder: str,
                      file_name: str, df: pd.DataFrame) -> str:
    extension_normal = ".csv"
    file_metadata = {
        'name': file_name + extension_normal,
        'parents': [parent_folder],
        'mimeType': 'text / csv'
    }
    buffer = io.BytesIO()
    df.to_csv(path_or_buf=buffer, sep=",", index=False, encoding="UTF-8")
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='text / csv')
    file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
    file_id = file.get("id")
    return file_id


def maintain_tokens():
    # delete old broken tokens - should run in the background
    service = authenticate()
    try:
        while True:
            items = search(query=f'"folder_session" in parents')
            if items:
                for item in items:
                    item_time = datetime.strptime(item["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    just_now = datetime.utcnow()
                    if just_now - item_time > timedelta(seconds=600):
                        try:
                            service.files().delete(fileId=item["id"]).execute()
                            log_info(f'maintain_tokens - Old token deleted: {item["name"]}')
                        except Exception as e:
                            log_error(f'maintain_tokens - Failed old token deleted: {item["name"]}. {e}')
            sleep(5)
    except KeyboardInterrupt:
        print("stopped!")


def create_token(service: googleapiclient.discovery.Resource) -> str:
    token = str(datetime.now())
    df_session = pd.DataFrame(["test"])
    while 0 == 0:
        try:
            session_folder_id = get_name("folder_session")
            token_id = save_new_csv_file(service, parent_folder=session_folder_id, file_name=token, df=df_session)
            log_info(f'create_token - created {token_id}')
            break
        except Exception as e:
            log_error(f'create_token - cannot save {token}. {e}')
            pass
    return token_id


def wait_for_my_turn(service: googleapiclient.discovery.Resource, token_id: str) -> int:
    # waits until this is the first token in time (wait till other threads finish)
    # find the token
    items = search(query=f'"folder_session" in parents')
    if not items:
        log_error(f'wait_for_my_turn - Token {token_id} disappeared!')
        return 0
    token_time = 0
    for item in items:
        if item["id"] == token_id:
            token_time = item["modifiedTime"]
            break
    if token_time == 0:
        log_error(f'wait_for_my_turn - Token {token_id} disappeared!')
        return 0

    # find old tokens and delete them - they exist because of previous interrupted operation
    for item in items:
        if item["modifiedTime"] - token_time > timedelta(seconds=600):
            try:
                service.files().delete(fileId=item["id"]).execute()
                log_info(f'wait_for_my_turn - Old token deleted: {item["name"]}')
            except Exception as e:
                log_error(f'wait_for_my_turn - Failed old token deleted: {item["name"]}. {e}')

    # wait till all older tokens are gone = other threads finished writing files
    waiting = 0
    oldest = True
    while oldest:
        items = search(query=f'"folder_session" in parents')
        if not items:
            log_error(f'wait_for_my_turn - Token {token_id} disappeared!')
            break
        for item in items:
            if token_time > item["modifiedTime"]:
                oldest = False
        if oldest:
            break
        waiting += 1
        oldest = True
    return waiting


def delete_token(service: googleapiclient.discovery.Resource, token_id: str) -> None:
    try:
        service.files().delete(fileId=token_id).execute()
        log_info(f'delete_token - successful {token_id}')
    except Exception as e:
        log_error(f'delete_token - Could not delete {token_id} - {e}')
