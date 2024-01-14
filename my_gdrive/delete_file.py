from my_gdrive import authenticate


def delete_file(file_id: str) -> None:
    try:
        service = authenticate()
    except ValueError:
        raise ValueError("Failed to delete file")
    service.files().delete(fileId=file_id).execute()
    return None
