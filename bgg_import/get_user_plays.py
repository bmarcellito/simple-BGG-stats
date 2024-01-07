from datetime import datetime
from io import StringIO
import pandas as pd
import streamlit as st

from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from bgg_import.import_xml_from_bgg import import_xml_from_bgg
from my_logger import log_error


def user_plays(username: str, refresh: int) -> (pd.DataFrame, str):
    """
    Importing all play instances uf a specific user from BGG website
    Has to import for every user separately, so used every time a new user is chosen
    :param username: BGG username
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    df = pd.DataFrame()

    q = (f'"folder_user" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = search(query=q)
    if not items:
        log_error(f'user_plays - No folder for user {username}. Cannot save collection.')
        return pd.DataFrame(), "Missing user folder"
    user_folder_id = items[0]["id"]

    q = f'"{user_folder_id}" in parents and name contains "user_plays"'
    item = search(query=q)
    if item:
        file_id = item[0]["id"]
        df = load_zip(file_id=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            feedback = f'Cached data loaded. It is {how_fresh} old. Number of plays: {len(df)}'
            # log_info(f'Plays of {username} loaded. It is {how_fresh} old.')
            return df, feedback

    # read the first page of play info from BGG
    result = import_xml_from_bgg(f'plays?username={username}')
    if result == "":
        return pd.DataFrame, "BGG website reading error"
    """ BGG returns 100 plays per page
    The top of the XML page stores the number of plays in total
    Here we find this number so we know how many pages to read
    """
    i = result.find("total=")
    total = int("".join(filter(str.isdigit, result[i + 7:i + 12])))
    if total == 0:
        feedback = f'User {username} haven\'t recorded any plays yet.'
        # log_info(f'Importing plays: user {username} has not recorded any plays yet.')
        return df, feedback
    page_no, rest = divmod(total, 100)
    if rest > 0:
        page_no += 1

    """The XML structure of plays are complicate, and cannot be read at once with Pandas
    So every page is parsed twice, into 2 dataframes
    df_play has the date, df_game has the name of the game
    At the end the 2 dataframes are concatenated 1:1
    """
    progress_text = "Importing plays..."
    step_all = page_no + 1
    step = 0
    my_bar = st.progress(0, text=progress_text)

    df_play = pd.read_xml(StringIO(result))
    df_game = pd.read_xml(StringIO(result), xpath=".//item")
    step += 1
    my_bar.progress(step // step_all, text=progress_text)

    while page_no > 1:
        result = import_xml_from_bgg(f'plays?username={username}&page={page_no}')
        if result == "":
            return pd.DataFrame, "BGG website reading error"
        df_play_next_page = pd.read_xml(StringIO(result))
        df_play = pd.concat([df_play, df_play_next_page])
        df_game_next_page = pd.read_xml(StringIO(result), xpath=".//item")
        df_game = pd.concat([df_game, df_game_next_page])
        page_no -= 1
        step += 1
        my_bar.progress(step * 100 // step_all, text=progress_text)

    df_play = pd.concat([df_play, df_game], axis=1).reset_index(drop=True)
    # remove parsed data not needed
    df_play = df_play.drop(["length", "incomplete", "nowinstats", "location", "objecttype", "subtypes", "item"], axis=1)
    if "players" in df_play.columns:
        df_play = df_play.drop(["players"], axis=1)
    df_play = df_play.sort_values(by=["date"])

    # removing plays that are recorded to future dates
    today = datetime.date(datetime.today())
    df_play = df_play.query(f'date <= "{today}"').reset_index()

    overwrite_background(parent_folder=user_folder_id, filename="user_plays", df=df_play)

    step += 1
    my_bar.progress(step * 100 // step_all, text=progress_text)
    my_bar.empty()
    feedback = f'Importing finished. Number of plays: {len(df_play)}'
    # log_info(f'Plays of {username} imported. Number of plays: {len(df_play)}')
    return df_play, feedback
