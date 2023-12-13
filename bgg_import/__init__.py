import re
import time
from datetime import datetime, timedelta
import requests
from io import StringIO
from xml.etree import ElementTree as ET
import pandas as pd
import streamlit as st
from threading import Thread
from streamlit.runtime.scriptrunner import add_script_run_ctx

import gdrive
from my_logger import logger, timeit

gdrive_original = st.secrets["gdrive_original"]
gdrive_processed = st.secrets["gdrive_processed"]
gdrive_user = st.secrets["gdrive_user"]
filename_current_ranking_source = "boardgames_list"
filename_current_ranking_processed = "current_ranking"
filename_historical_ranking_processed = "historical_ranking"
filename_game_infodb_processed = "game_infoDB"
filename_playnum_processed = "playnum_infoDB"


@timeit
def init_load() -> None:
    def init_current_ranking() -> None:
        for item in items:
            if item["name"] == "current_ranking.zip":
                st.session_state.global_fresh_ranking = gdrive.load_zip(item["id"])
                st.session_state.global_fresh_ranking.drop_duplicates(subset=["objectid"], keep="last",
                                                                      ignore_index=True, inplace=True)

    def init_game_infodb() -> None:
        for item in items:
            if item["name"] == "game_infoDB.zip":
                st.session_state.global_game_infodb = gdrive.load_zip(item["id"])
                st.session_state.global_game_infodb.drop_duplicates(subset=["objectid"], keep="last",
                                                                    ignore_index=True, inplace=True)

    def init_historic_ranking() -> None:
        for item in items:
            if item["name"] == "historical_ranking.zip":
                st.session_state.global_historic_ranking = gdrive.load_zip(item["id"])
                st.session_state.global_historic_ranking.query(expr="best_rank < 2000", inplace=True)
                st.session_state.global_historic_ranking.drop_duplicates(subset=["objectid"], keep="last",
                                                                         ignore_index=True, inplace=True)

    def init_play_numdb() -> None:
        for item in items:
            if item["name"] == "playnum_infoDB.zip":
                st.session_state.global_play_numdb = gdrive.load_zip(item["id"])
                st.session_state.global_play_numdb.drop_duplicates(subset=["objectid", "numplayers"], keep="last",
                                                                   ignore_index=True, inplace=True)

    def init_user_cache() -> None:
        for item in items:
            if item["name"] == "check_user_cache.zip":
                st.session_state.check_user_cache = gdrive.load_zip(item["id"])
                st.session_state.check_user_cache.drop_duplicates(subset=["username"], keep="last",
                                                                  ignore_index=True, inplace=True)

    q = f'"{gdrive_processed}" in parents'
    items = gdrive.search(query=q)
    if not items:
        pass
    else:
        thread_current_ranking = Thread(target=init_current_ranking)
        add_script_run_ctx(thread_current_ranking)
        thread_current_ranking.start()

        thread_game_infodb = Thread(target=init_game_infodb)
        add_script_run_ctx(thread_game_infodb)
        thread_game_infodb.start()

        thread_historic_ranking = Thread(target=init_historic_ranking)
        add_script_run_ctx(thread_historic_ranking)
        thread_historic_ranking.start()

        thread_play_numdb = Thread(target=init_play_numdb)
        add_script_run_ctx(thread_play_numdb)
        thread_play_numdb.start()

        thread_user_cache = Thread(target=init_user_cache)
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

    return None


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    while True:
        try:
            response = requests.get(f'https://boardgamegeek.com/xmlapi2/{link}', timeout=10)
        except requests.exceptions.HTTPError as err:
            logger.error(f'Http error: {err}. Link: {link}')
            continue
        except requests.exceptions.ConnectionError as err:
            logger.error(f'Error connecting: {err}. Link: {link}')
            continue
        except requests.exceptions.Timeout as err:
            logger.error(f'Timeout error: {err}. Link: {link}')
            continue
        except requests.exceptions.RequestException as err:
            logger.error(f'Other request error: {err}. Link: {link}')
            continue
        if response.status_code == 200:
            break
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        time.sleep(5)
    return response.content.decode(encoding="utf-8")


def check_user(username: str, df_check_user_cache: pd.DataFrame) -> (str, str, pd.DataFrame):
    st.caption("Checking user on BGG...")
    if username == "":
        return "Init", "", df_check_user_cache

    # check whether we have successfully found this username in the last month
    if not df_check_user_cache.empty:
        user_rows = df_check_user_cache.query(f'username == "{username}"').reset_index()
        if not user_rows.empty:
            old_enough = str(datetime.date(datetime.now() - timedelta(30)))
            if old_enough < user_rows.at[0, "last_checked"]:
                st.caption("User found in cache!")
                return "User found", "", df_check_user_cache

    # this user has not been checked in the last month
    global gdrive_user
    global gdrive_processed
    result = import_xml_from_bgg(f'collection?username={username}')
    try:
        df = pd.read_xml(StringIO(result))
    except ValueError:
        st.caption(f'No user found on bgg with this username: {username}')
        return "No valid user", "", df_check_user_cache
    if "message" in df.columns:
        st.caption(f'No user found on bgg with this username: {username}')
        return "No valid user", "", df_check_user_cache

    q = (f'"{gdrive_user}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = gdrive.search(query=q)
    if not items:
        gdrive.create_folder(parent_folder=gdrive_user, folder_name=username)
        logger.info(f'Folder created: {username}')
    st.caption("User found on BGG!")

    # add user info to cache
    new_cache_row = pd.DataFrame(data={"username": username, "last_checked": str(datetime.date(datetime.now()))},
                                 index=[0])

    if len(df_check_user_cache) == 0:
        df_check_user_cache = new_cache_row
    else:
        df_check_user_cache = pd.concat([df_check_user_cache, new_cache_row], ignore_index=True)
        df_check_user_cache.drop_duplicates(subset=["username"], keep="last", inplace=True)
    gdrive.save_background(parent_folder=gdrive_processed, filename="check_user_cache",
                           df=df_check_user_cache, concat=["username"])
    return "User found", result, df_check_user_cache


def delete_user_info(username: str) -> None:
    global gdrive_user
    q = (f'"{gdrive_user}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    folder_items = gdrive.search(query=q)
    if not folder_items:
        logger.info(f'Delete user: No folder to user: {username}, so no data to delete')
        return None

    items = gdrive.search(query=f'"{folder_items[0]["id"]}" in parents')
    if not items:
        logger.info(f'Delete user: No data to delete: {username}')
        return None
    else:
        for item in items:
            gdrive.delete_file(file_id=item["id"])

    logger.info(f'Delete user successfully: {username}')
    return None


# noinspection PyRedundantParentheses
@timeit
def current_ranking(current_ranking: pd.DataFrame) \
        -> pd.DataFrame:
    """
    There is no API on BGG for downloading all games and their current ranking
    However they upload a .csv file daily that has all the information
    This function reads such a file and removes unnecessary columns
    Changes monthly. User independent, enough to load at the start
    :return: imported data in dataframe
    """
    # st.caption("Importing list of board games...")
    global gdrive_original
    global gdrive_processed
    global filename_current_ranking_source
    global filename_current_ranking_processed

    q = (f'"{gdrive_original}" in parents and name contains "{filename_current_ranking_source}"')
    items_source = gdrive.search(query=q)
    if not items_source:
        source_last_modified = 0
        data_source = False
    else:
        source_last_modified = items_source[0]["modifiedTime"]
        data_source = True

    q = (f'"{gdrive_processed}" in parents and name contains "{filename_current_ranking_processed}"')
    items_processed = gdrive.search(query=q)
    if not items_processed:
        data_processed = False
        process_last_modified = 0
    else:
        data_processed = True
        process_last_modified = items_processed[0]["modifiedTime"]

    if (not data_source) and (not data_processed):
        # st.caption("Missing current ranking information!")
        logger.error(f'Current ranking info: No original & no processed data!')
        return pd.DataFrame()

    if (not data_source) and data_processed:
        # df = gdrive.load_zip(file_id=items_processed[0]["id"])
        # st.caption(f'Importing finished. Number of items: {len(df)}')
        # logger.info(f'Processed current ranking data loaded. No original data founded')
        # initial loading already loaded it.
        return current_ranking

    if data_source and data_processed:
        if process_last_modified > source_last_modified:
            # df = gdrive.load_zip(file_id=items_processed[0]["id"])
            # st.caption(f'Importing finished. Number of items: {len(df)}')
            # logger.info(f'Processed current ranking data loaded. No new original data founded')
            # initial loading already loaded it.
            return current_ranking

    df = gdrive.load_zip(file_id=items_source[0]["id"])
    df = df[["id", "name", "yearpublished", "rank", "abstracts_rank", "cgs_rank", "childrensgames_rank",
             "familygames_rank", "partygames_rank", "strategygames_rank", "thematic_rank", "wargames_rank"]]
    df.rename(columns={"id": "objectid"}, inplace=True)

    gdrive.overwrite_background(parent_folder=gdrive_processed, filename=filename_current_ranking_processed, df=df)
    # st.caption(f'Importing finished. Number of items: {len(df)}')
    logger.info(f'Found new current ranking data. It is imported. Number of items: {len(df)}')
    return df


# noinspection PyRedundantParentheses
@timeit
def historic_ranking(current_historic_ranking: pd.DataFrame) -> pd.DataFrame:
    """
    Importing the game rankings from multiple different dates
    Historic game ranking information cannot be accessed via API at BGG
    There are scrape files available for every day since 2016
    Filename convention: YYYY-MM-DD.csv
    This function loads the files one by one and add the ranking information as a new column
    The game IDs and names come from the game DB (downloaded by a different function)
    Changes monthly. User independent, enough to load at the start
    :param current_historic_ranking: current data available in the memory
    :return: imported data in dataframe
    """
    def sort_files(sort_by):
        return sort_by["name"]

    # st.caption("Importing historical game rankings")
    global gdrive_original
    global gdrive_processed
    global filename_historical_ranking_processed

    if len(current_historic_ranking) > 0:
        df_historical = current_historic_ranking
        existing_imports = df_historical.columns.values.tolist()
    else:
        df_historical = pd.DataFrame(columns=["objectid", "best_rank"])
        existing_imports = []

    # identifying the historical data files
    files_to_import = []
    items = gdrive.search(query=f'"{gdrive_original}" in parents')
    if not items:
        logger.info(f'Processed Historical rankings loaded. No historical original data found')
        return df_historical
    for item in items:
        if re.match(r'\d{4}-\d{2}-\d{2}', item['name']):
            name = item["name"]
            name_len = len(name)
            name = name[:name_len - 4]
            if not (name in existing_imports):
                files_to_import.append(item)
    files_to_import.sort(key=sort_files)
    if not files_to_import:
        if df_historical.empty:
            # st.caption(f'No game info list available, no processed historical game rankings available. '
            #            f'Cannot create historical game rankings data!')
            logger.error("No game info list available, no processed historical game rankings available.")
        else:
            # st.caption(f'Importing finished. Number of sampling: {len(existing_imports)}')
            logger.info(f'Historical ranking loaded. No new data')
        return df_historical

    # each iteration loads a file, and adds the ranking information from it as a column to the historical dataframe
    # progress_text = "Importing new historical game rankings file..."
    # step_all = len(files_to_import) + 1
    # my_bar = st.progress(0, text=progress_text)
    for step, i in enumerate(files_to_import):
        historical_loaded = gdrive.load_zip(file_id=i["id"])
        historical_loaded = historical_loaded[["ID", "Rank"]]
        column_name = i["name"]
        name_len = len(column_name)
        column_name = column_name[:name_len - 4]
        historical_loaded.rename(columns={"Rank": column_name}, inplace=True)
        historical_loaded.rename(columns={"ID": "objectid"}, inplace=True)
        df_historical = df_historical.merge(historical_loaded, on="objectid", how="outer")
        # my_bar.progress(step * 100 // step_all, text=progress_text)

    # reorder columns
    column_list = df_historical.columns.values.tolist()
    column_list[3:len(column_list)] = sorted(column_list[3:len(column_list)])
    df_historical = df_historical[column_list]

    """ merge created cells with Nan as there are no information to fill in
    This changes the data type from INT to FLOAT
    Here we add 0s and change back the data type to INT
    """
    df_historical.fillna(0, inplace=True)
    column_list = list(df_historical.columns.values)
    del column_list[:3]
    for i in column_list:
        df_historical = df_historical.astype({i: "int32"})
    df_historical = df_historical.reset_index()

    # find the highest rank for each item
    for i in range(len(df_historical)):
        row = df_historical.iloc[[i]].values.flatten().tolist()
        row_nonzero = [i for i in row if i != 0]
        df_historical.at[i, "best_rank"] = min(row_nonzero)

    # TODO: games with multiple ID issue

    gdrive.overwrite_background(parent_folder=gdrive_processed, filename=filename_historical_ranking_processed,
                                df=df_historical)

    # my_bar.empty()
    # st.caption(f'Importing finished. Number of sampling: {len(files_to_import)}')
    logger.info(f'New historical ranking found and imported.')
    return df_historical


def get_one_item_info(i):
    result = import_xml_from_bgg(f'thing?id={i}&stats=1')
    row_objectid = i
    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8")
    except ValueError:
        logger.error(f'Objectid: {i}. User has related record, however BGG miss this item!')
        return pd.DataFrame(), pd.DataFrame()
    row_type = df_item.iloc[0, 0]
    if row_type not in ("boardgame", "boardgameexpansion"):
        # this item is not a board game or expansion (BGG has video games and RPG related items as well)
        return pd.DataFrame(), pd.DataFrame()
    if "thumbnail" in df_item:
        row_thumbnail = df_item.iloc[0, 2]
    else:
        row_thumbnail = ""
    if "image" in df_item:
        row_image = df_item.iloc[0, 3]
    else:
        row_image = ""

    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//yearpublished")
        row_published = df_item.iloc[0, 0]
    except ValueError:
        logger.error(f'Objectid: {i} has no yearpublished info')
        row_published = 0

    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//minplayers")
        row_min_player = df_item.iloc[0, 0]
    except ValueError:
        logger.error(f'Objectid: {i} has no minplayers info')
        row_min_player = 0

    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//maxplayers")
        row_max_player = df_item.iloc[0, 0]
    except ValueError:
        logger.error(f'Objectid: {i} has no maxplayers info')
        row_max_player = 0

    df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//name")
    df_item = df_item.query('type == "primary"')
    row_name = df_item.iloc[0, 2]

    game_links = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//link")
    df_item = game_links.query('type == "boardgamedesigner"')
    row_designer = ', '.join(df_item["value"])

    if "inbound" in game_links:
        df_item = game_links.query('(type == "boardgameexpansion") and (inbound == "false")')
        row_expansion_of = ', '.join(df_item["value"])
    else:
        df_item = game_links.query('type == "boardgameexpansion"')
        row_expansion_of = ', '.join(df_item["value"])

    if "inbound" in game_links:
        df_item = game_links.query('(type == "boardgameexpansion") and (inbound == "true")')
        row_expansion_for = ', '.join(df_item["value"])
    else:
        row_expansion_for = ""

    game_rating = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//average")
    row_rating = game_rating.iloc[0, 0]

    game_weight = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//averageweight")
    row_weight = game_weight.iloc[0, 0]

    new_row = {"objectid": row_objectid,
               "name": row_name,
               "type": row_type,
               "year_published": row_published,
               "weight": row_weight,
               "rating_average": row_rating,
               "designer": row_designer,
               "expansion_of": row_expansion_of,
               "expansion_for": row_expansion_for,
               "thumbnail": row_thumbnail,
               "image": row_image,
               "min_player": row_min_player,
               "max_player": row_max_player}

    df_playnum = import_player_number(result, row_objectid)
    return new_row, df_playnum


def build_item_db_background():
    global gdrive_processed
    global filename_current_ranking_processed

    q = f'"{gdrive_processed}" in parents and name contains "{filename_current_ranking_processed}"'
    items_processed = ""
    while not items_processed:
        items_processed = gdrive.search(query=q)


# noinspection PyRedundantParentheses
def build_item_db(games_to_import_list: list, global_game_infodb: pd.DataFrame, global_play_numdb: pd.DataFrame) -> \
        (pd.DataFrame, pd.DataFrame):
    global gdrive_processed
    global filename_game_infodb_processed
    global filename_playnum_processed

    df_game_info = global_game_infodb
    df_playnumdb = global_play_numdb

    df_game_info = pd.DataFrame()
    df_playnumdb = pd.DataFrame()
    progress_text = "Reading game information..."
    my_bar = st.progress(0, text=progress_text)
    step_all = len(games_to_import_list)
    for step, i in enumerate(games_to_import_list):
        new_item_row, new_playnum_rows = get_one_item_info(i)
        if len(new_item_row) > 0:
            if df_game_info.empty:
                df_game_info = pd.DataFrame(new_item_row, index=[0])
            else:
                try:
                    df_game_info.loc[len(df_game_info)] = new_item_row
                except ValueError:
                    print(df_game_info.columns.values)
                    print("")
                    print(new_item_row)
                    exit(0)
        if len(new_playnum_rows) > 0:
            if df_playnumdb.empty:
                df_playnumdb = pd.DataFrame(new_playnum_rows, index=[0])
            else:
                df_playnumdb = pd.concat([df_playnumdb, new_playnum_rows], ignore_index=True)
        my_bar.progress((step+1) * 100 // step_all, text=progress_text)

    my_bar.empty()
    gdrive.save_background(parent_folder=gdrive_processed, filename=filename_game_infodb_processed,
                           df=df_game_info, concat=["objectid"])
    gdrive.save_background(parent_folder=gdrive_processed, filename=filename_playnum_processed,
                           df=df_playnumdb, concat=["objectid", "numplayers"])
    df_game_info = pd.concat([global_game_infodb, df_game_info], ignore_index=True)
    df_game_info.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
    df_playnumdb = pd.concat([global_play_numdb, df_playnumdb], ignore_index=True)
    df_playnumdb.drop_duplicates(subset=["objectid", "numplayers"], keep="last", ignore_index=True, inplace=True)

    st.caption(f'Importing finished. {len(games_to_import_list)} new item information saved.')
    return df_game_info, df_playnumdb


def build_item_db_all(df_new_games: pd.DataFrame, df_new_plays: pd.DataFrame, global_game_infodb: pd.DataFrame,
                      global_play_numdb: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
    if df_new_games.empty and df_new_plays.empty:
        return global_game_infodb, global_play_numdb
    if not df_new_games.empty:
        possible_new_items = df_new_games.groupby("objectid").count().reset_index()
        possible_new_items_list = possible_new_items["objectid"].tolist()
    else:
        possible_new_items_list = []
    if not df_new_plays.empty:
        possible_new_items = df_new_games.groupby("objectid").count().reset_index()
        possible_new_items_list = possible_new_items_list + possible_new_items["objectid"].tolist()

    # remove duplicates
    possible_new_items_list = list(set(possible_new_items_list))
    st.caption("Importing detailed item information for user's collection...")

    games_to_import_list = []
    if len(global_game_infodb) > 0:
        existing_item_list = global_game_infodb["objectid"].tolist()
        for i in possible_new_items_list:
            if i not in existing_item_list:
                games_to_import_list.append(i)
    else:
        games_to_import_list = possible_new_items_list
    if not games_to_import_list:
        return global_game_infodb, global_play_numdb

    chunk = 100
    for i in range((len(games_to_import_list) // chunk)+1):
        import_part = games_to_import_list[i*chunk:(i+1)*chunk]
        placeholder = st.empty()
        with placeholder.container():
            st.caption(f'{len(games_to_import_list)-i*chunk} items left')
            df_game_info, df_playnumdb = build_item_db(import_part, global_game_infodb, global_play_numdb)
        placeholder.empty()
    return df_game_info, df_playnumdb


def import_player_number(result: str, objectid: str) -> pd.DataFrame:
    df_playnum = pd.DataFrame(columns=["objectid", "numplayers", "best", "recommended", "not recommended"])

    root = ET.fromstring(result)
    root = root.find("item")
    minplayers = int(root.find("minplayers").attrib["value"])
    maxplayers = int(root.find("maxplayers").attrib["value"])
    max_player_to_import = min(8, maxplayers)
    root = root.find("poll")
    for child in root:
        try:
            numplayers = int(child.attrib["numplayers"])
        except ValueError:
            continue
        if minplayers <= numplayers <= max_player_to_import:
            best = 0
            recom = 0
            not_recom = 0
            for grandchildren in child:
                match grandchildren.attrib["value"]:
                    case "Best":
                        best = grandchildren.attrib["numvotes"]
                    case "Recommended":
                        recom = grandchildren.attrib["numvotes"]
                    case "Not Recommended":
                        not_recom = grandchildren.attrib["numvotes"]
            data = {
                "objectid": [objectid],
                "numplayers": [numplayers],
                "best": [best],
                "recommended": [recom],
                "not recommended": [not_recom]
            }
            new_row = pd.DataFrame(data)
            df_playnum = pd.concat([df_playnum, new_row], ignore_index=True)
    return df_playnum


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def user_collection(username: str, user_page: str, refresh: int) -> pd.DataFrame:
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
    :param user_page: previously loaded user collection page
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    st.caption(f'Importing collection of {username}...')
    global gdrive_user
    filename = f'collection_{username}'

    q = (f'"{gdrive_user}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = gdrive.search(query=q)
    if not items:
        logger.error(f'No folder for user {username}. Cannot save collection.')
        return pd.DataFrame()
    user_folder_id = items[0]["id"]

    q = f'"{user_folder_id}" in parents and name contains "{filename}"'
    item = gdrive.search(query=q)
    if item:
        file_id = item[0]["id"]
        df = gdrive.load_zip(file_id=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of games in collection: {len(df)}')
            logger.info(f'Collection of {username} loaded. It is {how_fresh} old.')
            return df

    if len(user_page) == 0:
        result = import_xml_from_bgg(f'collection?username={username}&stats=1')
    else:
        result = user_page

    # Game name and general game information
    df = pd.read_xml(StringIO(result))
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
        logger.error(f'df_rating xpath //rating error.')
        df_rating = pd.DataFrame(columns=["user_rating"])
        for i in range(len(df)):
            df_rating.at[i, 0] = 0
    df = pd.concat([df, df_rating], axis=1).reset_index(drop=True)

    # User information related to the games, like owned, ...
    df_status = pd.read_xml(StringIO(result), xpath=".//status")
    df = pd.concat([df, df_status], axis=1).reset_index(drop=True)

    df = df.sort_values("yearpublished").reset_index()
    gdrive.overwrite_background(parent_folder=user_folder_id, filename=filename, df=df)

    st.caption(f'Collection imported. Number of games + expansions known: {len(df)}')
    logger.info(f'Collection of {username} imported. Number of items: {len(df)}')
    return df


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def user_plays(username: str, refresh: int) -> pd.DataFrame:
    """
    Importing all play instances uf a specific user from BGG website
    Has to import for every user separately, so used every time a new user is chosen
    :param username: BGG username
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    st.caption(f'Importing plays of {username}...')
    df = pd.DataFrame()
    global gdrive_user
    filename = f'plays_{username}'

    q = (f'"{gdrive_user}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = gdrive.search(query=q)
    if not items:
        logger.error(f'No folder for user {username}. Cannot save collection.')
        return pd.DataFrame()
    user_folder_id = items[0]["id"]

    q = (f'"{user_folder_id}" in parents and name contains "{filename}"')
    item = gdrive.search(query=q)
    if item:
        file_id = item[0]["id"]
        df = gdrive.load_zip(file_id=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of plays: {len(df)}')
            logger.info(f'Plays of {username} loaded. It is {how_fresh} old.')
            return df

    # read the first page of play info from BGG
    result = import_xml_from_bgg(f'plays?username={username}')
    """ BGG returns 100 plays per page
    The top of the XML page stores the number of plays in total
    Here we find this number so we know how many pages to read
    """
    i = result.find("total=")
    total = int("".join(filter(str.isdigit, result[i + 7:i + 12])))
    if total == 0:
        st.caption(f'User {username} haven\'t recorded any plays yet.')
        logger.info(f'Importing plays: user {username} has not recorded any plays yet.')
        return df
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
    df_play = df_play.sort_values(by=["date"]).reset_index()

    gdrive.save_background(parent_folder=user_folder_id, filename=filename, df=df_play, concat=["id"])

    step += 1
    my_bar.progress(step * 100 // step_all, text=progress_text)
    my_bar.empty()
    st.caption(f'Importing finished. Number of plays: {len(df_play)}')
    logger.info(f'Plays of {username} imported. Number of plays: {len(df_play)}')
    return df_play
