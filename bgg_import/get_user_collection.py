from datetime import datetime
from io import StringIO
import pandas as pd

from my_gdrive.search import search
from my_gdrive.create_folder import create_folder
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from bgg_import.import_xml_from_bgg import import_xml_from_bgg
from my_logger import log_info, log_error


def user_collection(username: str, refresh: int) -> (pd.DataFrame, str):
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
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    q = (f'"folder_user" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = search(query=q)
    if not items:
        log_error(f'user_collection - No folder for user {username}. Cannot save collection.')
        user_folder_id = create_folder(parent_folder="folder_user", folder_name=username)
    else:
        user_folder_id = items[0]["id"]

    q = f'"{user_folder_id}" in parents and name contains "user_collection"'
    item = search(query=q)
    if item:
        file_id = item[0]["id"]
        df = load_zip(file_id=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            feedback = f'Cached data loaded. It is {how_fresh} old. Number of items in collection: {len(df)}'
            log_info(f'Collection of {username} loaded. It is {how_fresh} old.')
            return df, feedback

    result = import_xml_from_bgg(f'collection?username={username}&stats=1')

    # Game name and general game information
    try:
        df = pd.read_xml(StringIO(result))
    except ValueError:
        return pd.DataFrame(), "Some error happened :("
    df = df[["objectid", "name", "yearpublished", "numplays"]]
    # filling missing publishing years
    df["yearpublished"] = df["yearpublished"].fillna(0)
    df["yearpublished"] = df["yearpublished"].astype(int)

    # User ratings
    try:
        df_rating = pd.read_xml(StringIO(result), xpath=".//rating")
        df_rating = pd.DataFrame(df_rating["value"])
        df_rating.rename(columns={"value": "user_rating"}, inplace=True)
    except ValueError:
        log_error(f'user_collection - df_rating xpath //rating error.')
        df_rating = pd.DataFrame(columns=["user_rating"])
        for i in range(len(df)):
            df_rating.at[i, 0] = 0
    df = pd.concat([df, df_rating], axis=1).reset_index(drop=True)

    # User information related to the games, like owned, ...
    df_status = pd.read_xml(StringIO(result), xpath=".//status")
    df = pd.concat([df, df_status], axis=1).reset_index(drop=True)

    df = df.sort_values("yearpublished").reset_index()
    overwrite_background(parent_folder=user_folder_id, filename="user_collection", df=df)

    feedback = f'Collection imported. Number of games + expansions known: {len(df)}'
    log_info(f'Collection of {username} imported. Number of items: {len(df)}')
    return df, feedback
