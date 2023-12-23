import io
import pandas as pd
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload

from my_gdrive import authenticate
from my_gdrive.constants import extension_compressed
from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions.token_mgmt import create_token, wait_for_my_turn, delete_token
from my_logger import logger


def save_new_zip_file(service: googleapiclient.discovery.Resource, parent_folder: str,
                      file_name: str, df: pd.DataFrame):
    file_metadata = {
        'name': file_name + extension_compressed,
        'parents': [parent_folder],
        'mimeType': 'application/zip'
    }
    buffer = io.BytesIO()
    df.to_csv(path_or_buf=buffer, sep=",", index=False, encoding="UTF-8",
              compression={'method': 'zip', "archive_name": f"{file_name}.csv", 'compresslevel': 6})
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='application/zip')
    file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
    file_id = file.get("id")
    return file_id


def save(gdrive_folder: str, gdrive_filename: str, df: pd.DataFrame, concat: list) -> str:
    service = authenticate()
    my_token = create_token(service)
    wait_for_my_turn(my_token)
    # now it is possible to change files
    q = f'"{gdrive_folder}" in parents and name contains "{gdrive_filename}"'
    items = search(query=q)
    if not items:
        # create new file as there is no existing one
        file_id = save_new_zip_file(service=service, parent_folder=gdrive_folder, file_name=gdrive_filename, df=df)
        logger.info(f'File saved: {gdrive_filename}')
        delete_token(service, my_token)
        return file_id
    # overwrite existing file
    existing_file_id = items[0]["id"]
    df_existing = load_zip(file_id=items[0]["id"])
    if len(concat) > 0:
        df_merged = pd.concat([df_existing, df], ignore_index=True)
        df_merged.drop_duplicates(subset=concat, keep="last", inplace=True, ignore_index=True)
    else:
        df_merged = df_existing
    try:
        service.files().delete(fileId=existing_file_id).execute()
    except Exception as e:
        logger.error(f'Cannot delete {gdrive_filename}. {e}')
    try:
        file_id = save_new_zip_file(service=service, parent_folder=gdrive_folder, file_name=gdrive_filename, df=df_merged)
    except Exception as e:
        logger.error(f'Cannot save {gdrive_filename}. {e}')
        file_id = ""
    logger.info(f'File overwritten: {gdrive_filename}')
    delete_token(service, my_token)
    return file_id
