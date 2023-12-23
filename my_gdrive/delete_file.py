from my_gdrive import authenticate


def delete_file(file_id: str) -> None:
    service = authenticate()
    service.files().delete(fileId=file_id).execute()
    return None
