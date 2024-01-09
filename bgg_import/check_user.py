from datetime import datetime, timedelta
from io import StringIO
import pandas as pd
import streamlit as st

from my_gdrive.search import search
from my_gdrive.create_folder import create_folder
from my_gdrive.save_functions import save_background
from bgg_import.import_xml_from_bgg import import_xml_from_bgg
from bgg_import.get_functions import get_username_cache
from bgg_import.delete_user_info import delete_user_info


class BggUserRequest:
    def __init__(self, status: str, response: str, folder_id: str):
        self.status = status
        self.response = response
        self.folder_id = folder_id


def is_user_in_cache(username, df_username_cache) -> str:
    # check whether we have successfully found this username
    if df_username_cache.empty:
        return ""

    refresh_in_days = st.secrets["refresh_user_cache"]
    user_rows = df_username_cache.query(f'username == "{username}"').reset_index()
    if user_rows.empty:
        return ""

    old_enough = str(datetime.date(datetime.now() - timedelta(days=refresh_in_days)))
    if old_enough < user_rows.at[0, "last_checked"]:
        return user_rows.at[0, "folder_id"]
    else:
        delete_user_info(username, user_rows.at[0, "folder_id"])
        return ""


def is_user_on_bgg(username: str) -> (BggUserRequest, str):
    ph_is_user = st.empty()
    ph_is_user.caption(f'Checking user on BGG website...')
    answer = import_xml_from_bgg(f'user?name={username}')
    if not answer.status:
        return BggUserRequest("Error", answer.response, ""), ""
    start = answer.data.find("id=") + 4
    end = answer.data.find("\"", start)
    if end == start:
        ph_is_user.caption(f'No user found on BGG with this username: {username}')
        return BggUserRequest("Not_found", "", ""), ""
    ph_is_user.caption("User found on BGG!")
    return BggUserRequest("Found", "", ""), answer.data


def import_user_info(username: str, result: str, folder_id: str) -> pd.DataFrame:
    start = result.find("id=") + 4
    end = result.find("\"", start)
    user_id = int("".join(filter(str.isdigit, result[start:end])))
    try:
        df = pd.read_xml(StringIO(result), xpath=".//firstname")
        if len(df) > 0:
            first_name = df.iloc[0, 0]
            if first_name != first_name:
                first_name = ""
        else:
            first_name = ""
    except ValueError:
        first_name = ""
    try:
        df = pd.read_xml(StringIO(result), xpath=".//lastname")
        if len(df) > 0:
            last_name = df.iloc[0, 0]
            if last_name != last_name:
                last_name = ""
        else:
            last_name = ""
    except ValueError:
        last_name = ""
    try:
        df = pd.read_xml(StringIO(result), xpath=".//yearregistered")
        if len(df) > 0:
            year_registered = df.iloc[0, 0]
            if year_registered != year_registered:
                year_registered = ""
        else:
            year_registered = ""
    except ValueError:
        year_registered = ""
    try:
        df = pd.read_xml(StringIO(result), xpath=".//country")
        if len(df) > 0:
            country = df.iloc[0, 0]
            if country != country:
                country = ""
        else:
            country = ""
    except ValueError:
        country = ""

    # add user info to cache
    just_now = str(datetime.date(datetime.now()))
    new_cache_row = pd.DataFrame(data={
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "year_registered": year_registered,
        "country": country,
        "folder_id": folder_id,
        "last_checked": just_now}, index=[0])
    return new_cache_row


def save_user_info(new_cache_row: pd.DataFrame, df_username_cache: pd.DataFrame) -> pd.DataFrame:
    if len(df_username_cache) == 0:
        df_username_cache = new_cache_row
    else:
        df_username_cache = pd.concat([df_username_cache, new_cache_row], ignore_index=True)
        df_username_cache.drop_duplicates(subset=["user_id"], keep="last", inplace=True)
    save_background(parent_folder="folder_processed", filename="check_user_cache",
                    df=df_username_cache, concat=["user_id"])
    return df_username_cache


def create_user_folder(username: str) -> str:
    q = (f'"folder_user" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = search(query=q)
    if items:
        for item in items:
            delete_user_info(username, item["id"])
    folder_id = create_folder(parent_folder="folder_user", folder_name=username)
    return folder_id


def check_user(username: str) -> BggUserRequest:
    if username == "":
        return BggUserRequest("No_user_selected", "No username was entered", "")
    df_username_cache = get_username_cache()

    folder_id = is_user_in_cache(username, df_username_cache.data)
    if len(folder_id) != 0:
        st.caption("User found in cache!")
        return BggUserRequest("User_found", "Username found in cache", folder_id)

    answer, data = is_user_on_bgg(username)
    if answer == "Not_found":
        return BggUserRequest("No_valid_user", "Username was not found on BGG", "")
    if answer == "Error":
        return BggUserRequest("Import_error", answer.response, "")

    folder_id = create_user_folder(username)
    new_cache_row = import_user_info(username, data, folder_id)
    new_cache = save_user_info(new_cache_row, df_username_cache.data)
    df_username_cache.data = new_cache
    return BggUserRequest("User_found", "Username found on Bgg", folder_id)
