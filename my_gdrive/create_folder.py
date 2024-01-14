from my_gdrive import authenticate
from my_gdrive.constants import replace_names


def create_folder(parent_folder: str, folder_name: str) -> str:
    try:
        service = authenticate()
    except ValueError:
        raise ValueError("Failed creating folder")
    updated_parent_folder = replace_names(parent_folder)
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [updated_parent_folder]
    }
    file = service.files().create(body=file_metadata, fields="id").execute()
    folder_id = file.get("id")
    return folder_id
