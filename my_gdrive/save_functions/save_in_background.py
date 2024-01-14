import io
import pandas as pd
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload

from my_gdrive import authenticate
from my_gdrive.search import file_search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions.token_mgmt import create_token, wait_for_my_turn, delete_token
from my_logger import log_error


def save_new_zip_file(service: googleapiclient.discovery.Resource, parent_folder: str,
                      file_name: str, df: pd.DataFrame):
    extension_normal = ".csv"
    extension_compressed = ".zip"
    file_metadata = {
        'name': file_name + extension_compressed,
        'parents': [parent_folder],
        'mimeType': 'application/zip'
    }
    buffer = io.BytesIO()
    df.to_csv(path_or_buf=buffer, sep=",", index=False, encoding="UTF-8",
              compression={'method': 'zip', "archive_name": f"{file_name}{extension_normal}", 'compresslevel': 6})
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='application/zip')
    try:
        file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
        file_id = file.get("id")
        return file_id
    except Exception as error:
        log_error(f'save_new_zip_file - Error saving: {type(error)}')


def save(gdrive_folder: str, gdrive_filename: str, df: pd.DataFrame, concat: list) -> str:
    try:
        service = authenticate()
    except ValueError:
        log_error(f'save - Failed to save because of authentication error! Filename: {gdrive_filename}')
        return ""

    my_token = create_token(service)
    try:
        wait_for_my_turn(service, my_token)
    except ValueError:
        log_error(f'save - Failed to save because of token error! Filename: {gdrive_filename}')
        return ""

    # now it is possible to change files
    q = f'"{gdrive_folder}" in parents and name contains "{gdrive_filename}"'
    try:
        items = file_search(query=q)
    except ValueError:
        log_error(f'save - Failed to save because of search error! Filename: {gdrive_filename}')
        return ""

    if not items:
        # create new file as there is no existing one
        file_id = save_new_zip_file(service=service, parent_folder=gdrive_folder, file_name=gdrive_filename, df=df)
        delete_token(service, my_token)
        return file_id

    # overwrite existing file
    existing_file_id = items[0]["id"]
    if len(concat) > 0:
        try:
            df_existing = load_zip(file_id=items[0]["id"])
        except ValueError:
            log_error(f'save - Failed to save because could not load existing file! Filename: {gdrive_filename}')
            return ""
        df_merged = pd.concat([df_existing, df], ignore_index=True)
        df_merged.drop_duplicates(subset=concat, keep="last", inplace=True, ignore_index=True)
    else:
        df_merged = df

    try:
        service.files().delete(fileId=existing_file_id).execute()
    except Exception as error:
        log_error(f'save - Cannot delete existing file: {gdrive_filename}. {error}')

    try:
        file_id = save_new_zip_file(service=service, parent_folder=gdrive_folder, file_name=gdrive_filename,
                                    df=df_merged)
    except Exception as error:
        log_error(f'save - Cannot save new file: {gdrive_filename}. {error}')
        file_id = ""

    delete_token(service, my_token)
    return file_id
