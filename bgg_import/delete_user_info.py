from my_gdrive.delete_file import delete_file
from my_gdrive.search import search_native
from my_logger import log_info


def delete_user_info(username: str, folder_id: str) -> None:
    items = search_native(query=f'"{folder_id}" in parents')
    if not items:
        log_info(f'delete_user_info - Delete user: No data to delete: {username}')
        return None

    for item in items:
        delete_file(file_id=item["id"])
    delete_file(folder_id)
    log_info(f'Delete user successfully: {username}')
    return None
