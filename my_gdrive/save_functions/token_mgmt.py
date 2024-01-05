import io
from datetime import datetime, timedelta
from time import sleep
import googleapiclient.discovery
import pandas as pd
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
                            log_info(f'Old token deleted: {item["name"]}')
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
            break
        except Exception as e:
            log_error(f'create_token - Cannot save {token}. {e}')
            pass
    return token_id


def wait_for_my_turn(token_id: str) -> int:
    # waits until this is the first token in time (wait till other threads finish)
    waiting = 0
    while 0 == 0:
        items = search(query=f'"folder_session" in parents')
        if not items:
            log_error(f'wait_for_my_turn - Token {token_id} disappeared!')
            break
        first_token_id = items[0]["id"]
        first_token_time = items[0]["modifiedTime"]
        for item in items:
            if first_token_time > item["modifiedTime"]:
                first_token_id = item["id"]
                first_token_time = item["modifiedTime"]
        if first_token_id == token_id:
            break
        waiting += 1
    return waiting


def delete_token(service: googleapiclient.discovery.Resource, token_id: str) -> None:
    try:
        service.files().delete(fileId=token_id).execute()
    except Exception as e:
        log_error(f'delete_token - Could not delete {token_id} - {e}')
