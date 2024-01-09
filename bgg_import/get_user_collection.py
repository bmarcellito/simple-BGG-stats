from datetime import datetime, timezone
from io import StringIO
import pandas as pd
import streamlit as st

from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from bgg_import.import_xml_from_bgg import import_xml_from_bgg
from my_logger import log_info, log_error


class UserCollection:
    def __init__(self, status: bool, import_msg: str, df: pd.DataFrame):
        self.status = status
        self.import_msg = import_msg
        self.data = df


@st.cache_resource(show_spinner=False, ttl=3600)
def get_user_collection(username: str, folder_id: str) -> UserCollection:
    refresh_user_data = st.secrets["refresh_user_data"]
    imported_user_collection = import_user_collection(username, folder_id, refresh_user_data)
    return imported_user_collection


def import_user_collection(username: str, user_folder_id: str, refresh: int) -> UserCollection:
    """
    BGG adds all game you have interacted with into a collection
    Interaction: played with, rated, commented
    Attributes of a game in collection: Owned, Previously owned, For trade, Played with, ...
    Processed data is stored at: processed_path\\BGG_username (separate from other users' data)
    Data is imported from BGG website if the last import happened more than a week ago,
    otherwise the previously processed & saved data files loaded
    Data can change fast, like daily.
    Has to import for every user separately, so used every time a new user is chosen
    The XML structure of plays are complicate, and cannot be read at once with Pandas
    So it is parsed twice, into 2 dataframes: df has the game information, df_status has the attributes
    At the end the 2 dataframes are concatenated 1:1
    :param username: user ID of the specific user
    :param user_folder_id: ID of the user's folder where the cache is stored
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    q = f'"{user_folder_id}" in parents and name contains "user_collection"'
    item = search(query=q)
    if item:
        file_id = item[0]["id"]
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            df = load_zip(file_id=file_id)
            import_msg = f'Cached collection loaded. Number of items: {len(df)}.'
            log_info(f'Collection of {username} loaded. It is {how_fresh.days} days old.')
            return UserCollection(True, import_msg, df)

    answer = import_xml_from_bgg(f'collection?username={username}&stats=1')
    if not answer.status:
        return UserCollection(False, answer.response, pd.DataFrame())
    # Game name and general game information
    try:
        df = pd.read_xml(StringIO(answer.data))
    except Exception as err:
        return UserCollection(False, str(type(err)), pd.DataFrame())
    df = df[["objectid", "name", "yearpublished", "numplays"]]
    # filling missing publishing years
    df["yearpublished"] = df["yearpublished"].fillna(0)
    df["yearpublished"] = df["yearpublished"].astype(int)

    # User ratings
    try:
        df_rating = pd.read_xml(StringIO(answer.data), xpath=".//rating")
        df_rating = pd.DataFrame(df_rating["value"])
        df_rating.rename(columns={"value": "user_rating"}, inplace=True)
    except ValueError:
        log_error(f'user_collection - df_rating xpath //rating error.')
        df_rating = pd.DataFrame(columns=["user_rating"])
        for i in range(len(df)):
            df_rating.at[i, 0] = 0
    df = pd.concat([df, df_rating], axis=1).reset_index(drop=True)

    # User information related to the games, like owned, ...
    df_status = pd.read_xml(StringIO(answer.data), xpath=".//status")
    df = pd.concat([df, df_status], axis=1).reset_index(drop=True)

    df = df.sort_values("yearpublished").reset_index()
    overwrite_background(parent_folder=user_folder_id, filename="user_collection", df=df)

    feedback = f'Collection imported. Number of items: {len(df)}.'
    log_info(f'Collection of {username} imported. Number of items: {len(df)}')
    return UserCollection(True, feedback, df)
