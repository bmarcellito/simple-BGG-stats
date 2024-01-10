from datetime import datetime, timezone
from io import StringIO
import pandas as pd
import streamlit as st

from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from bgg_import.import_xml_from_bgg import import_xml_from_bgg


class UserPlays:
    def __init__(self, status: bool, import_msg: str, df: pd.DataFrame):
        self.status = status
        self.import_msg = import_msg
        self.data = df


@st.cache_resource(show_spinner=False, ttl=3600)
def get_user_plays(username: str, folder_id: str) -> UserPlays:
    refresh_user_data = st.secrets["refresh_user_data"]
    imported_plays = import_user_plays(username, folder_id, refresh_user_data)
    return imported_plays


def import_user_plays(username: str, user_folder_id, refresh: int) -> UserPlays:
    """
    Importing all play instances uf a specific user from BGG website
    Has to import for every user separately, so used every time a new user is chosen
    :param username: BGG username
    :param user_folder_id: ID of the user's folder where the cached data is stored
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    if refresh > 0:
        q = f'"{user_folder_id}" in parents and name contains "user_plays"'
        item = search(query=q)
        if item:
            file_id = item[0]["id"]
            last_imported = item[0]["modifiedTime"]
            last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
            how_fresh = datetime.now() - last_imported
            if how_fresh.days < refresh:
                df = load_zip(file_id=file_id)
                import_msg = f'Cached data loaded. Number of plays: {len(df)}'
                return UserPlays(True, import_msg, df)

    # read the first page of play info from BGG
    answer = import_xml_from_bgg(f'plays?username={username}')
    if not answer.status:
        return UserPlays(False, answer.response, pd.DataFrame())
    """ BGG returns 100 plays per page
    The top of the XML page stores the number of plays in total
    Here we find this number so we know how many pages to read
    """
    i = answer.data.find("total=")
    total = int("".join(filter(str.isdigit, answer.data[i + 7:i + 12])))
    if total == 0:
        import_msg = f'User {username} haven\'t recorded any plays yet.'
        return UserPlays(True, import_msg, pd.DataFrame())
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

    df_play = pd.read_xml(StringIO(answer.data))
    df_game = pd.read_xml(StringIO(answer.data), xpath=".//item")
    step += 1
    my_bar.progress(step // step_all, text=progress_text)

    while page_no > 1:
        answer = import_xml_from_bgg(f'plays?username={username}&page={page_no}')
        if not answer:
            my_bar.empty()
            return UserPlays(False, "BGG website reading error", pd.DataFrame())
        try:
            df_play_next_page = pd.read_xml(StringIO(answer.data))
        except SyntaxError as err:
            my_bar.empty()
            print("-----------------------------")
            print(page_no)
            print(answer.data)
            print("-----------------------------")
            return UserPlays(False, f'Syntax error: {type(err)}, {err}', pd.DataFrame())
        except Exception as err:
            my_bar.empty()
            return UserPlays(False, str(type(err)), pd.DataFrame())
        df_play = pd.concat([df_play, df_play_next_page])
        df_game_next_page = pd.read_xml(StringIO(answer.data), xpath=".//item")
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
    import_msg = f'Importing finished. Number of plays: {len(df_play)}'
    # log_info(f'Plays of {username} imported. Number of plays: {len(df_play)}')
    return UserPlays(True, import_msg, df_play)
