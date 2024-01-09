import pandas as pd
import streamlit as st

from my_gdrive.constants import get_name
from my_gdrive.load_functions import load_zip
from my_gdrive.search import search


class GameInfo:
    def __init__(self, df: pd.DataFrame, import_text):
        self.data = df
        self.import_text = import_text


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_game_infodb() -> GameInfo:
    df = pd.DataFrame()
    filename = get_name("game_infodb")
    q = f'"folder_processed" in parents and name contains "{filename}"'
    items = search(query=q)
    if not items:
        pass
    else:
        for item in items:
            if filename in item["name"]:
                df = load_zip(item["id"])
                df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
    return GameInfo(df, "")


class PlayNo:
    def __init__(self, df: pd.DataFrame, import_text):
        self.data = df
        self.import_text = import_text


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_play_no_db() -> PlayNo:
    df = pd.DataFrame()
    filename = get_name("playnum_infodb")
    q = f'"folder_processed" in parents and name contains "{filename}"'
    items = search(query=q)
    if not items:
        pass
    else:
        for item in items:
            if filename in item["name"]:
                df = load_zip(item["id"])
                df.drop_duplicates(subset=["objectid", "numplayers"], keep="last", ignore_index=True, inplace=True)
    return PlayNo(df, "")


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_current_rankings() -> pd.DataFrame:
    df = pd.DataFrame()
    filename = get_name("current_ranking_processed")
    q = f'"folder_processed" in parents and name contains "{filename}"'
    items = search(query=q)
    if not items:
        pass
    else:
        for item in items:
            if filename in item["name"]:
                df = load_zip(item["id"])
                df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
    return df


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_historic_rankings() -> pd.DataFrame:
    df = pd.DataFrame()
    filename = get_name("historical_ranking_processed")
    q = f'"folder_processed" in parents and name contains "{filename}"'
    items = search(query=q)
    if not items:
        pass
    else:
        for item in items:
            if filename in item["name"]:
                df = load_zip(item["id"])
                df.query(expr="best_rank < 2000", inplace=True)
                df.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
    return df


class UsernameCache:
    def __init__(self, df: pd.DataFrame, import_text):
        self.data = df
        self.import_text = import_text


@st.cache_resource(show_spinner=False, ttl=24*3600)
def get_username_cache() -> UsernameCache:
    df = pd.DataFrame()
    filename = get_name("check_user_cache")
    q = f'"folder_processed" in parents and name contains "{filename}"'
    items = search(query=q)
    if not items:
        pass
    else:
        for item in items:
            if filename in item["name"]:
                df = load_zip(item["id"])
                df.drop_duplicates(subset=["username"], keep="last", ignore_index=True, inplace=True)
    return UsernameCache(df, "")
