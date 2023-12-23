import streamlit as st

folders = {
    "folder_original": st.secrets["gdrive_original"],
    "folder_processed": st.secrets["gdrive_processed"],
    "folder_user": st.secrets["gdrive_user"],
    "folder_session": st.secrets["gdrive_session"]
}

filenames = {
    "current_ranking_source": "boardgames_list",
    "current_ranking_processed": "current_ranking",
    "historical_ranking_processed": "historical_ranking",
    "game_infodb": "game_infoDB",
    "playnum_infodb": "playnum_infoDB",
    "user_collection": "collection",
    "user_plays": "plays",
    "check_user_cache": "check_user_cache"
}

extension_normal = ".csv"
extension_compressed = ".zip"

private_key_id = st.secrets["private_key_id"]
private_key = st.secrets["private_key"]
client_email = st.secrets["client_email"]
client_id = st.secrets["client_id"]


def replace_names(text: str) -> str:
    for key in filenames:
        text = text.replace(key, filenames[key])
    for key in folders:
        text = text.replace(key, folders[key])
    return text


def get_name(text: str) -> str:
    for key in filenames:
        if text == key:
            return filenames[key]
    for key in folders:
        if text == key:
            return folders[key]
    return ""
