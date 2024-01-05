from my_gdrive.delete_file import delete_file
from my_gdrive.search import search
from my_logger import log_error


def delete_user_info(username: str) -> None:
    q = (f'"folder_user" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    folder_items = search(query=q)
    if not folder_items:
        log_error(f'delete_user_info - Delete user: No folder to user: {username}, so no data to delete')
        return None

    items = search(query=f'"{folder_items[0]["id"]}" in parents')
    if not items:
        log_error(f'delete_user_info - Delete user: No data to delete: {username}')
        return None
    else:
        for item in items:
            delete_file(file_id=item["id"])

    # log_info(f'Delete user successfully: {username}')
    return None
