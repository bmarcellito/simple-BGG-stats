from threading import Thread
import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions.token_mgmt import maintain_tokens
from my_gdrive.constants import get_name


def init_current_ranking(items: list) -> None:
    filename = get_name("current_ranking_processed")
    for item in items:
        if filename in item["name"]:
            st.session_state.global_fresh_ranking = load_zip(item["id"])
            st.session_state.global_fresh_ranking.drop_duplicates(subset=["objectid"], keep="last",
                                                                  ignore_index=True, inplace=True)


def init_game_infodb(items: list) -> None:
    filename = get_name("game_infodb")
    for item in items:
        if filename in item["name"]:
            st.session_state.global_game_infodb = load_zip(item["id"])
            st.session_state.global_game_infodb.drop_duplicates(subset=["objectid"], keep="last",
                                                                ignore_index=True, inplace=True)


def init_historic_ranking(items: list) -> None:
    filename = get_name("historical_ranking_processed")
    for item in items:
        if filename in item["name"]:
            st.session_state.global_historic_ranking = load_zip(item["id"])
            st.session_state.global_historic_ranking.query(expr="best_rank < 2000", inplace=True)
            st.session_state.global_historic_ranking.drop_duplicates(subset=["objectid"], keep="last",
                                                                     ignore_index=True, inplace=True)


def init_play_numdb(items: list) -> None:
    filename = get_name("playnum_infodb")
    for item in items:
        if filename in item["name"]:
            st.session_state.global_play_numdb = load_zip(item["id"])
            st.session_state.global_play_numdb.drop_duplicates(subset=["objectid", "numplayers"], keep="last",
                                                               ignore_index=True, inplace=True)


def init_user_cache(items: list) -> None:
    filename = get_name("check_user_cache")
    for item in items:
        if filename in item["name"]:
            st.session_state.check_user_cache = load_zip(item["id"])
            st.session_state.check_user_cache.drop_duplicates(subset=["username"], keep="last",
                                                              ignore_index=True, inplace=True)


def init_token_maintenance() -> None:
    maintain_tokens()


def init_load() -> None:
    q = f'"folder_processed" in parents'
    items = search(query=q)
    if not items:
        pass
    else:
        thread_current_ranking = Thread(target=init_current_ranking, args=(items,))
        thread_current_ranking.name = "init_current_ranking"
        add_script_run_ctx(thread_current_ranking)
        thread_current_ranking.start()

        thread_game_infodb = Thread(target=init_game_infodb, args=(items,))
        thread_game_infodb.name = "init_game_infodb"
        add_script_run_ctx(thread_game_infodb)
        thread_game_infodb.start()

        thread_historic_ranking = Thread(target=init_historic_ranking, args=(items,))
        thread_historic_ranking.name = "init_historic_ranking"
        add_script_run_ctx(thread_historic_ranking)
        thread_historic_ranking.start()

        thread_play_numdb = Thread(target=init_play_numdb, args=(items,))
        thread_play_numdb.name = "init_play_numdb"
        add_script_run_ctx(thread_play_numdb)
        thread_play_numdb.start()

        thread_user_cache = Thread(target=init_user_cache, args=(items,))
        thread_user_cache.name = "init_user_cache"
        add_script_run_ctx(thread_user_cache)
        thread_user_cache.start()

        thread_user_cache.join()
        thread_play_numdb.join()
        thread_current_ranking.join()
        thread_game_infodb.join()
        thread_historic_ranking.join()

    if "global_fresh_ranking" not in st.session_state:
        st.session_state.global_fresh_ranking = pd.DataFrame()
    if "global_game_infodb" not in st.session_state:
        st.session_state.global_game_infodb = pd.DataFrame()
    if "global_historic_ranking" not in st.session_state:
        st.session_state.global_historic_ranking = pd.DataFrame()
    if "global_play_numdb" not in st.session_state:
        st.session_state.global_play_numdb = pd.DataFrame()
    if "check_user_cache" not in st.session_state:
        st.session_state.check_user_cache = pd.DataFrame()

    thread_maintain_tokens = Thread(target=init_token_maintenance)
    thread_maintain_tokens.name = "maintain_tokens"
    add_script_run_ctx(thread_maintain_tokens)
    thread_maintain_tokens.start()
    return None
