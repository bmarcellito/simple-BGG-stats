from threading import Thread
import pandas as pd
from streamlit.runtime.scriptrunner import add_script_run_ctx

from my_gdrive.save_functions.save_in_background import save
from my_gdrive.constants import replace_names


def save_background(parent_folder: str, filename: str, df: pd.DataFrame, concat: list) -> None:
    updated_parent_folder = replace_names(parent_folder)
    updated_filename = replace_names(filename)
    thread_save = Thread(target=save, args=(updated_parent_folder, updated_filename, df, concat))
    thread_save.name = f"save_{parent_folder}/{filename}"
    add_script_run_ctx(thread_save)
    thread_save.start()
    return None


def overwrite_background(parent_folder: str, filename: str, df: pd.DataFrame) -> None:
    updated_parent_folder = replace_names(parent_folder)
    updated_filename = replace_names(filename)
    print(f'{updated_parent_folder}/{updated_filename}')
    thread_overwrite = Thread(target=save, args=(updated_parent_folder, updated_filename, df, []))
    thread_overwrite.name = f"save_{parent_folder}/{filename}"
    add_script_run_ctx(thread_overwrite)
    thread_overwrite.start()
    return None
