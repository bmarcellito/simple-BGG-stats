import streamlit as st


def get_gdrive_folders() -> dict:
    folders = {
        "folder_original": st.secrets["gdrive_original"],
        "folder_processed": st.secrets["gdrive_processed"],
        "folder_user": st.secrets["gdrive_user"],
        "folder_session": st.secrets["gdrive_session"]
    }
    return folders


def get_gdrive_filenames() -> dict:
    filenames = {
        "current_ranking_source": "boardgames_list",
        "current_ranking_processed": "current_ranking",
        "historical_ranking_processed": "historical_ranking",
        "game_infodb": "game_infoDB",
        "playnum_infodb": "playnum_infoDB",
        "user_collection": "collection",
        "user_plays": "plays",
        "check_user_cache": "check_user_cache",
        "feedbacks": "feedbacks"
    }
    return filenames


def replace_names(text: str) -> str:
    filenames = get_gdrive_filenames()
    for key in filenames:
        text = text.replace(key, filenames[key])
    folders = get_gdrive_folders()
    for key in folders:
        text = text.replace(key, folders[key])
    return text


def get_name(text: str) -> str:
    filenames = get_gdrive_filenames()
    for key in filenames:
        if text == key:
            return filenames[key]
    folders = get_gdrive_folders()
    for key in folders:
        if text == key:
            return folders[key]
    return ""
