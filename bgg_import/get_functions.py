import pandas as pd
import streamlit as st

from my_gdrive.constants import get_name
from my_gdrive.load_functions import load_zip
from my_gdrive.search import file_search


class GameInfo:
    def __init__(self, df: pd.DataFrame, import_msg):
        self.data = df
        self.import_msg = import_msg


def find_processed_file(filename_to_search: str) -> str:
    q = f'"folder_processed" in parents and name contains "{filename_to_search}"'
    try:
        items = file_search(query=q)
    except ValueError:
        raise ValueError("Failed to find file")
    if not items:
        return ""

    file_id = ""
    for item in items:
        if filename_to_search in item["name"]:
            file_id = item["id"]
            break
    return file_id


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_game_infodb() -> GameInfo:
    filename = get_name("game_infodb")
    try:
        file_id = find_processed_file(filename)
    except ValueError:
        return GameInfo(pd.DataFrame(), "Failed to load")
    if file_id == "":
        return GameInfo(pd.DataFrame(), "No previously saved information")

    try:
        df = load_zip(file_id)
        df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
        import_msg = "Successfully loaded"
        return GameInfo(df, import_msg)
    except ValueError:
        return GameInfo(pd.DataFrame(), "Failed to load")


class PlayNo:
    def __init__(self, df: pd.DataFrame, import_msg):
        self.data = df
        self.import_msg = import_msg


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_play_no_db() -> PlayNo:
    filename = get_name("playnum_infodb")
    try:
        file_id = find_processed_file(filename)
    except ValueError:
        return PlayNo(pd.DataFrame(), "Failed to load")
    if file_id == "":
        return PlayNo(pd.DataFrame(), "No previously saved information")

    try:
        df = load_zip(file_id)
        df.drop_duplicates(subset=["objectid", "numplayers"], keep="last", ignore_index=True, inplace=True)
        import_msg = "Successfully loaded"
        return PlayNo(df, import_msg)
    except ValueError:
        return PlayNo(pd.DataFrame(), "Failed to load")


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_current_rankings() -> pd.DataFrame:
    filename = get_name("current_ranking_processed")
    try:
        file_id = find_processed_file(filename)
    except ValueError:
        return pd.DataFrame()
    if file_id == "":
        return pd.DataFrame()

    try:
        df = load_zip(file_id)
        df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
        return df
    except ValueError:
        return pd.DataFrame()


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_historic_rankings() -> pd.DataFrame:
    filename = get_name("historical_ranking_processed")
    try:
        file_id = find_processed_file(filename)
    except ValueError:
        return pd.DataFrame()
    if file_id == "":
        return pd.DataFrame()

    try:
        df = load_zip(file_id)
        df.query(expr="best_rank < 2000", inplace=True)
        df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
        return df
    except ValueError:
        return pd.DataFrame()


class UsernameCache:
    def __init__(self, df: pd.DataFrame, import_msg):
        self.data = df
        self.import_msg = import_msg


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_username_cache() -> UsernameCache:
    filename = get_name("check_user_cache")
    try:
        file_id = find_processed_file(filename)
    except ValueError:
        return UsernameCache(pd.DataFrame(), "Failed to load")
    if file_id == "":
        return UsernameCache(pd.DataFrame(), "No previously saved information")

    try:
        df = load_zip(file_id)
        df.drop_duplicates(subset=["username"], keep="last", ignore_index=True, inplace=True)
        import_msg = "Successfully loaded"
        return UsernameCache(df, import_msg)
    except ValueError:
        return UsernameCache(pd.DataFrame(), "Failed to load")
