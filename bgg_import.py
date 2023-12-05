import re
import time
from datetime import datetime
from io import StringIO
from xml.etree import ElementTree as ET

import googleapiclient.discovery
import pandas as pd

import requests
import streamlit as st

import gdrive


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    while True:
        response = requests.get(f'https://boardgamegeek.com/xmlapi2/{link}')
        if response.status_code == 200:
            break
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        time.sleep(5)
    return response.content.decode(encoding="utf-8")


@st.cache_data(show_spinner=False)
def check_user(_service: googleapiclient.discovery.Resource, username: str, user_folder: str, _logger) -> (bool, str):
    st.caption("Checking user on BGG...")
    result = import_xml_from_bgg(f'collection?username={username}')
    try:
        df = pd.read_xml(StringIO(result))
    except ValueError:
        st.caption(f'No user found on bgg with this username: {username}')
        return False, ""
    if "message" in df.columns:
        st.caption(f'No user found on bgg with this username: {username}')
        return False, ""

    q = (f'"{user_folder}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    items = gdrive.search(_service, query=q)
    if not items:
        user_folder = gdrive.create_folder(_service, parent_folder=user_folder, folder_name=username)
        _logger.info(f'Folder created: {username}')
    st.caption("User found on BGG!")
    return True, user_folder


def delete_user_info(_service: googleapiclient.discovery.Resource, username: str, _logger) -> None:
    general_user_folder_id = st.secrets["gdrive_user"]
    q = (f'"{general_user_folder_id}" in parents and mimeType = "application/vnd.google-apps.folder" '
         f'and name contains "{username}"')
    folder_items = gdrive.search(_service, query=q)
    if not folder_items:
        _logger.info(f'Delete user: No folder to user: {username}, so no data to delete')
        return None

    items = gdrive.search(_service, query=f'"{folder_items[0]["id"]}" in parents')
    if not items:
        _logger.info(f'Delete user: No data to delete: {username}')
        return None
    else:
        for item in items:
            gdrive.delete_file(_service, item["id"])

    _logger.info(f'Delete user successfully: {username}')
    return None


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def current_ranking(_service: googleapiclient.discovery.Resource, path_original: str, path_processed: str, _logger) \
        -> pd.DataFrame:
    """
    There is no API on BGG for downloading all games and their current ranking
    However they upload a .csv file daily that has all the information
    This function reads such a file and removes unnecessary columns
    Changes monthly. User independent, enough to load at the start
    :param _service: Google Drive
    :param path_original:
    :param path_processed: where should the processed data be saved
    :param _logger: logging handler
    :return: imported data in dataframe
    """
    st.caption("Importing list of board games...")
    filename_source = "boardgames_list.csv"
    filename_processed = "current_ranking.csv"

    q = (f'"{path_original}" in parents and name contains "{filename_source}"')
    items_source = gdrive.search(_service, q)
    if not items_source:
        _logger.info(f'No fresh ranking source file')
        source_last_modified = 0
        data_source = False
    else:
        _logger.info(f'Fresh ranking source file found')
        source_last_modified = items_source[0]["modifiedTime"]
        data_source = True

    q = (f'"{path_processed}" in parents and name contains "{filename_processed}"')
    items_processed = gdrive.search(_service, q)
    if not items_processed:
        _logger.info(f'No processed fresh ranking ')
        data_processed = False
        process_last_modified = 0
    else:
        _logger.info(f'Processed fresh ranking found')
        data_processed = True
        process_last_modified = items_processed[0]["modifiedTime"]

    if (not data_source) and (not data_processed):
        st.caption("Missing current ranking information!")
        _logger.error(f'Current ranking info: No original & no processed data!')
        return pd.DataFrame()

    if (not data_source) and data_processed:
        df = gdrive.load(_service, items_processed[0]["id"], _logger)
        st.caption(f'Importing finished. Number of items: {len(df)}')
        _logger.info(f'Processed current ranking data loaded. No original data founded')
        return df

    if data_source and data_processed:
        if process_last_modified > source_last_modified:
            df = gdrive.load(_service, items_processed[0]["id"], _logger)
            st.caption(f'Importing finished. Number of items: {len(df)}')
            _logger.info(f'Processed current ranking data loaded. No new original data founded')
            return df

    df = gdrive.load(_service, items_source[0]["id"], _logger)
    df = df[["id", "name", "yearpublished", "rank", "abstracts_rank", "cgs_rank", "childrensgames_rank",
             "familygames_rank", "partygames_rank", "strategygames_rank", "thematic_rank", "wargames_rank"]]
    df.rename(columns={"id": "objectid"}, inplace=True)

    gdrive.save(_service, path_processed, filename_processed, df, False, _logger)
    st.caption(f'Importing finished. Number of games: {len(df)}')
    _logger.info(f'Found new current ranking data. It is imported')
    return df


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def historic_ranking(_service: googleapiclient.discovery.Resource, path_original: str, path_processed: str,
                     game_list: pd.DataFrame, _logger) -> pd.DataFrame:
    """
    Importing the game rankings from multiple different dates
    Historic game ranking information cannot be accessed via API at BGG
    There are scrape files available for every day since 2016
    Filename convention: YYYY-MM-DD.csv
    This function loads the files one by one and add the ranking information as a new column
    The game IDs and names come from the game DB (downloaded by a different function)
    Changes monthly. User independent, enough to load at the start
    :param _service: Google Drive
    :param path_original: where are the data scrape files
    :param path_processed: where should the processed data be saved
    :param game_list: list of all games in a dataframe
    :param _logger: logging handler
    :return: imported data in dataframe
    """

    def sort_files(sort_by):
        return sort_by["name"]

    st.caption("Importing historical game rankings")
    filename = "historical_ranking.csv"

    q = (f'"{path_processed}" in parents and name contains "{filename}"')
    items = gdrive.search(_service, q)
    if not items:
        _logger.info("No processed historical game rankings")
        existing_imports = []
        # game DB is the start of the historical dataframe
        if not game_list.empty:
            df_historical = game_list[["objectid", "name", "yearpublished"]].set_index("objectid")
        else:
            df_historical = pd.DataFrame(columns=["objectid", "name", "yearpublished"])
    else:
        _logger.info("processed Importing historical game rankings found")
        df_historical = gdrive.load(_service, items[0]["id"], _logger)
        existing_imports = df_historical.columns.values.tolist()
        del existing_imports[:3]

    # identifying the historical data files
    files_to_import = []
    items = gdrive.search(_service, query=f'"{path_original}" in parents')
    if not items:
        _logger.info(f'Historical ranking imported. No historical original data found')
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
            _logger.error("No game info list available, no processed historical game rankings available. "
                          "Cannot create historical game rankings data!")
        else:
            st.caption(f'Importing finished. Number of sampling: {len(existing_imports)}')
            _logger.info(f'Historical ranking imported. No new data')
        return df_historical

    _logger.info("historical original data found")
    # each iteration loads a file, and adds the ranking information from it as a column to the historical dataframe
    progress_text = "Importing new historical game rankings file..."
    step_all = len(files_to_import) + 1
    step = 0
    my_bar = st.progress(0, text=progress_text)
    for i in files_to_import:
        historical_loaded = gdrive.load(_service, i["id"], _logger)
        historical_loaded = historical_loaded[["ID", "Rank"]]
        column_name = i["name"]
        name_len = len(column_name)
        column_name = column_name[:name_len - 4]
        historical_loaded.rename(columns={"Rank": column_name}, inplace=True)
        historical_loaded.rename(columns={"ID": "objectid"}, inplace=True)
        df_historical = df_historical.merge(historical_loaded, on="objectid", how="outer")
        step += 1
        my_bar.progress(step * 100 // step_all, text=progress_text)

    # reorder columns
    column_list = list(df_historical.columns.values)
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

    # TODO: games with multiple ID issue

    gdrive.save(_service, path_processed, filename, df_historical, False, _logger)

    my_bar.empty()
    st.caption(f'Importing finished. Number of sampling: {len(files_to_import)}')
    _logger.info(f'New historical ranking found and imported.')
    return df_historical


# noinspection PyRedundantParentheses
def build_game_db(_service: googleapiclient.discovery.Resource, path_processed: str,
                  df_new: pd.DataFrame, _logger):
    if "user_rating" in df_new.columns.values:
        st.caption("Importing detailed game information for user's collection...")
    else:
        st.caption("Importing detailed game information for user's plays...")

    filename_game = "game_infoDB.csv"
    filename_playnum = "playnum_infoDB.csv"

    q = (f'"{path_processed}" in parents and name contains "{filename_game}"')
    items = gdrive.search(_service, q)
    if not items:
        df_game_info = pd.DataFrame()
    else:
        previous_game_file_id = items[0]["id"]
        df_game_info = gdrive.load(_service, previous_game_file_id, _logger)

    q = (f'"{path_processed}" in parents and name contains "{filename_playnum}"')
    items = gdrive.search(_service, q)
    if not items:
        df_playnumdb = pd.DataFrame()
    else:
        previous_play_file_id = items[0]["id"]
        df_playnumdb = gdrive.load(_service, previous_play_file_id, _logger)

    # first we loaded the existing files, so we can still return data if the request is empty
    if df_new.empty:
        _logger.info(f'Request for additional item info sent empty datafile. No new info items')
        return df_game_info, df_playnumdb

    possible_new_items = df_new.groupby("objectid").count().reset_index()
    possible_new_items_list = possible_new_items["objectid"].tolist()

    games_to_import_list = []
    if not df_game_info.empty:
        for i in possible_new_items_list:
            if i not in df_game_info["objectid"].values:
                games_to_import_list.append(i)
    else:
        games_to_import_list = possible_new_items_list
    if not games_to_import_list:
        _logger.info(f'Item info loaded. No new item info needed')
        return df_game_info, df_playnumdb

    progress_text = "Reading game information..."
    my_bar = st.progress(0, text=progress_text)
    step = 0
    step_all = len(games_to_import_list)
    for i in games_to_import_list:
        result = import_xml_from_bgg(f'thing?id={i}&stats=1')
        row_objectid = i

        df_item = pd.read_xml(StringIO(result), encoding="utf-8")
        row_type = df_item.iloc[0, 0]
        if "thumbnail" in df_item:
            row_thumbnail = df_item.iloc[0, 2]
        else:
            row_thumbnail = ""
        if "image" in df_item:
            row_image = df_item.iloc[0, 3]
        else:
            row_image = ""

        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//yearpublished")
        row_published = df_item.iloc[0, 0]

        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//minplayers")
        row_min_player = df_item.iloc[0, 0]

        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//maxplayers")
        row_max_player = df_item.iloc[0, 0]

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

        if df_game_info.empty:
            df_game_info = pd.DataFrame(new_row, index=[0])
        else:
            df_game_info.loc[len(df_game_info)] = new_row
        step += 1
        df_playnumdb = import_player_number(df_playnumdb, result, row_objectid)
        my_bar.progress(step * 100 // step_all, text=progress_text)
    my_bar.empty()

    gdrive.save(_service, path_processed, filename_game, df_game_info, True, _logger)
    gdrive.save(_service, path_processed, filename_playnum, df_playnumdb, True, _logger)

    st.caption(f'Importing finished. {len(games_to_import_list)} new game information saved.')
    _logger.info(f'New item info imported')
    return df_game_info, df_playnumdb


def import_player_number(df_playnumdb: pd.DataFrame, result: str, objectid: str) -> pd.DataFrame:
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
    df_playnum = pd.concat([df_playnumdb, df_playnum], ignore_index=True)
    return df_playnum


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def user_collection(_service: googleapiclient.discovery.Resource, username: str, path_user: str,
                    refresh: int, _logger) -> pd.DataFrame:
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
    :param _service: Google Drive
    :param username: user ID of the specific user
    :param path_user:
    :param refresh: if the previously imported data is older in days, new import will happen
    :param _logger: logging handler
    :return: imported data in dataframe
    """
    st.caption(f'Importing collection of {username}...')
    filename = f'collection_{username}.csv'

    q = (f'"{path_user}" in parents and name contains "{filename}"')
    item = gdrive.search(_service, query=q)
    if item:
        file_id = item[0]["id"]
        df = gdrive.load(service=_service, file_name=file_id, logger=_logger)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of games in collection: {len(df)}')
            _logger.info(f'Collection of {username} loaded. No importing as it is fresh enough')
            return df

    result = import_xml_from_bgg(f'collection?username={username}&stats=1')

    # Game name and general game information
    df = pd.read_xml(StringIO(result))
    df = df[["objectid", "name", "yearpublished", "numplays"]]
    # filling missing publishing years
    df["yearpublished"] = df["yearpublished"].fillna(0)
    df["yearpublished"] = df["yearpublished"].astype(int)

    # User ratings
    df_rating = pd.read_xml(StringIO(result), xpath=".//rating")
    df_rating = pd.DataFrame(df_rating["value"])
    df_rating.rename(columns={"value": "user_rating"}, inplace=True)
    df = pd.concat([df, df_rating], axis=1).reset_index(drop=True)

    # User information related to the games, like owned, ...
    df_status = pd.read_xml(StringIO(result), xpath=".//status")
    df = pd.concat([df, df_status], axis=1).reset_index(drop=True)

    df = df.sort_values("yearpublished").reset_index()

    gdrive.save(_service, path_user, filename, df, False, _logger)

    st.caption(f'Collection imported. Number of games + expansions known: {len(df)}')
    _logger.info(f'Collection of {username} imported')
    return df


# noinspection PyRedundantParentheses
@st.cache_data(show_spinner=False)
def user_plays(_service: googleapiclient.discovery.Resource, username: str, path_user: str,
               refresh: int, _logger) -> pd.DataFrame:
    """
    Importing all play instances uf a specific user from BGG website
    Has to import for every user separately, so used every time a new user is chosen
    :param _service: Google Drive
    :param username: BGG username
    :param path_user:
    :param refresh: if the previously imported data is older in days, new import will happen
    :param _logger: logging handler
    :return: imported data in dataframe
    """
    st.caption(f'Importing plays of {username}...')
    df = pd.DataFrame()
    filename = f'plays_{username}.csv'

    q = (f'"{path_user}" in parents and name contains "{filename}"')
    item = gdrive.search(_service, query=q)
    if item:
        file_id = item[0]["id"]
        df = gdrive.load(service=_service, file_name=file_id, logger=_logger)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of plays: {len(df)}')
            _logger.info(f'Plays of {username} loaded. It is fresh enough, no import')
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
        _logger.info(f'User {username} haven\'t recorded any plays yet.')
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

    gdrive.save(_service, path_user, filename, df_play, True, _logger)

    step += 1
    my_bar.progress(step * 100 // step_all, text=progress_text)
    my_bar.empty()
    st.caption(f'Importing finished. Number of plays: {len(df_play)}')
    _logger.info(f'Plays of {username} imported')
    return df_play
