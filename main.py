import requests  # reading websites
import time
from io import StringIO
import xml.etree.ElementTree as ET

# dataframes
import pandas as pd

# reading historical scraped files
from datetime import datetime, timedelta

# WEB interface
import streamlit as st
import plotly.express as px

# google drive
import googleapiclient.discovery
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
import io
import re


@st.cache_data
def gdrive_authenticate() -> googleapiclient.discovery.Resource:
    scopes = ['https://www.googleapis.com/auth/drive']
    service_account_info = {
        "type": "service_account",
        "project_id": "simple-bgg-stat-service-acc",
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/simple-bgg-stat-sa%40simple-bgg-stat-service-acc.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)
    return service


def gdrive_create_folder(service: googleapiclient.discovery.Resource, parent_folder: str, folder_name: str) -> str:
    file_metadata2 = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder]
    }
    file = service.files().create(body=file_metadata2, fields="id").execute()
    folder_id = file.get("id")
    return folder_id


def gdrive_save_file(service: googleapiclient.discovery.Resource,
                     parent_folder: str, file_name: str, df: pd.DataFrame) -> str:
    file_metadata = {
        'name': file_name,
        'parents': [parent_folder],
        'mimeType': 'text / csv'
    }
    buffer = io.BytesIO()
    df.to_csv(buffer, sep=",", index=False, encoding="UTF-8")
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='text / csv')
    file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
    file_id = file.get("id")
    return file_id


# noinspection PyTypeChecker
def gdrive_complex_save_file(service: googleapiclient.discovery.Resource,
                             parent_folder: str, filename: str, df: pd.DataFrame) -> str:
    def create_token() -> str:
        # create token
        token = str(datetime.now())
        df_session = pd.DataFrame(["test"])
        q = f'mimeType = "application/vnd.google-apps.folder" and name contains "session_id"'
        folder_items = gdrive_search(service, q)
        session_folder_id = folder_items[0]["id"]
        token_id = gdrive_save_file(service, parent_folder=session_folder_id, file_name=token, df=df_session)
        # waits until this is the first token (no other token is created earlier)
        while 0 == 0:
            token_items = gdrive_search(service, query=f'"{session_folder_id}" in parents')
            if not token_items:
                continue
            first_token_id = ""
            first_token_time = ""
            for item in token_items:
                if first_token_id == "":
                    first_token_id = item["id"]
                    first_token_time = item["modifiedTime"]
                if first_token_time > item["modifiedTime"]:
                    first_token_id = item["id"]
                    first_token_time = item["modifiedTime"]
            if first_token_id == token_id:
                break
        # ready to go
        return token_id

    def delete_token(token: str) -> None:
        gdrive_delete_file(service, token)

    items = gdrive_search(service, f'name contains "{filename}"')
    if not items:
        # create new file
        file_id = gdrive_save_file(service, parent_folder, filename, df)
    else:
        # overwrite existing file
        existing_file_id = items[0]["id"]
        my_token = create_token()
        df_existing = gdrive_load_file(service, items[0]["id"])
        df_merged = pd.concat([df_existing, df], ignore_index=True)
        df_merged = df_merged.drop_duplicates()
        gdrive_delete_file(service, existing_file_id)
        file_id = gdrive_save_file(service, parent_folder, filename, df_merged)
        delete_token(my_token)
    return file_id


def gdrive_delete_file(service: googleapiclient.discovery.Resource, file_id: str) -> None:
    service.files().delete(fileId=file_id).execute()
    return None


def gdrive_search(service: googleapiclient.discovery.Resource, query: str):
    results = service.files().list(q=query, fields="files(id, name, modifiedTime)").execute()
    return results.get('files', [])


def gdrive_load_file(service, file_name: str) -> pd.DataFrame:
    try:
        request = service.files().get_media(fileId=file_name)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
    source = io.StringIO(file.getvalue().decode(encoding='utf-8', errors='ignore'))
    df = pd.read_csv(source)
    return df


def import_xml_from_bgg(link: str) -> str:
    # HTTP request from boardgamegeek.com
    while True:
        response = requests.get(f'https://boardgamegeek.com/xmlapi2/{link}')
        if response.status_code == 200:
            break
        # BGG cannot handle huge amount of requests. Let's give it some rest!
        time.sleep(5)
    return response.content.decode(encoding="utf-8")


@st.cache_data
def check_bgg_user(_service: googleapiclient.discovery.Resource, username: str, path: str) -> bool:
    result = import_xml_from_bgg(f'collection?username={username}')
    try:
        df = pd.read_xml(StringIO(result))
    except ValueError:
        st.write(f'No user found on bgg with this username: {username}')
        return False

    if "message" in df.columns:
        st.write(f'No user found on bgg with this username: {username}')
        return False

    q = f'mimeType = "application/vnd.google-apps.folder" and name contains "{username}"'
    items = gdrive_search(_service, query=q)
    if not items:
        gdrive_create_folder(_service, parent_folder=path, folder_name=username)

    return True


# noinspection PyTypeChecker
@st.cache_data(ttl=86400)
def import_current_ranking(_service: googleapiclient.discovery.Resource, path_processed: str) -> pd.DataFrame:
    """
    There is no API on BGG for downloading all games and their current ranking
    However they upload a .csv file daily that has all the information
    This function reads such a file and removes unnecessary columns
    Changes monthly. User independent, enough to load at the start
    :param _service: Google Drive
    :param path_processed: where should the processed data be saved
    :return: imported data in dataframe
    """
    st.caption("Importing list of board games...")
    filename_source = "boardgames_ranks.csv"
    filename_processed = "current_ranking.csv"

    items_source = gdrive_search(_service, f'name contains "{filename_source}"')
    if not items_source:
        source_last_modified = 0
        data_source = False
    else:
        source_last_modified = items_source[0]["modifiedTime"]
        data_source = True

    items_processed = gdrive_search(_service, f'name contains "{filename_processed}"')
    if not items_processed:
        data_processed = False
        process_last_modified = 0
    else:
        data_processed = True
        process_last_modified = items_processed[0]["modifiedTime"]

    if (not data_source) and (not data_processed):
        st.caption("Missing current ranking information!")
        return pd.DataFrame()

    if (not data_source) and data_processed:
        df = gdrive_load_file(_service, items_processed[0]["id"])
        st.caption(f'Importing finished. Number of games: {len(df)}')
        return df

    if data_source and data_processed:
        if process_last_modified > source_last_modified:
            df = gdrive_load_file(_service, items_processed[0]["id"])
            return df

    df = gdrive_load_file(_service, items_source[0]["id"])
    df = df[["id", "name", "yearpublished", "rank", "abstracts_rank", "cgs_rank", "childrensgames_rank",
             "familygames_rank", "partygames_rank", "strategygames_rank", "thematic_rank", "wargames_rank"]]
    df.rename(columns={"id": "objectid"}, inplace=True)

    gdrive_complex_save_file(_service, path_processed, filename_processed, df)
    # UPDATED
    # if data_processed:
    #     gdrive_overwrite_file(_service, file_name=items_processed[0]["id"], df=df)
    # else:
    #     gdrive_save_file(_service, parent_folder=path_processed, file_name="current_ranking.csv", df=df)
    st.caption(f'Importing finished. Number of games: {len(df)}')
    return df


# noinspection PyTypeChecker
@st.cache_data(ttl=86400)
def import_historic_ranking(_service: googleapiclient.discovery.Resource, path_source: str, path_processed: str,
                            game_list: pd.DataFrame) -> pd.DataFrame:
    """
    Importing the game rankings from multiple different dates
    Historic game ranking information cannot be accessed via API at BGG
    There are scrape files available for every day since 2016
    Filename convention: YYYY-MM-DD.csv
    This function loads the files one by one and add the ranking information as a new column
    The game IDs and names come from the game DB (downloaded by a different function)
    Changes monthly. User independent, enough to load at the start
    :param _service: Google Drive
    :param path_source: where are the data scrape files
    :param path_processed: where should the processed data be saved
    :param game_list: list of all games in a dataframe
    :return: imported data in dataframe
    """
    def sort_files(sort_by):
        return sort_by["name"]

    st.caption("Importing historical game rankings")
    filename = "historical_ranking.csv"

    items = gdrive_search(_service, f'name contains "{filename}"')
    if not items:
        existing_imports = []
        # game DB is the start of the historical dataframe
        df_historical = game_list[["objectid", "name", "yearpublished"]].set_index("objectid")
    else:
        df_historical = gdrive_load_file(_service, items[0]["id"])
        existing_imports = df_historical.columns.values.tolist()
        del existing_imports[:3]

    # identifying the historical data files
    files_to_import = []
    items = gdrive_search(_service, query=f'"{path_source}" in parents')
    if not items:
        return df_historical
    for item in items:
        if re.match(r'\d{4}-\d{2}-\d{2}', item['name']):
            name = item["name"]
            name_len = len(name)
            name = name[:name_len-4]
            if not (name in existing_imports):
                files_to_import.append(item)
    files_to_import.sort(key=sort_files)
    if not files_to_import:
        st.caption(f'Importing finished. Number of sampling: {len(existing_imports)}')
        return df_historical

    # TODO new game appears in  a new historic file - what will happen?

    # each iteration loads a file, and adds the ranking information from it as a column to the historical dataframe
    progress_text = "Importing new historical game rankings file..."
    step_all = len(files_to_import)+1
    step = 0
    my_bar = st.progress(0, text=progress_text)
    for i in files_to_import:
        historical_loaded = gdrive_load_file(_service, i["id"])
        historical_loaded = historical_loaded[["ID", "Rank"]]
        column_name = i["name"]
        name_len = len(column_name)
        column_name = column_name[:name_len-4]
        historical_loaded.rename(columns={"Rank": column_name}, inplace=True)
        historical_loaded.rename(columns={"ID": "objectid"}, inplace=True)
        df_historical = df_historical.merge(historical_loaded, on="objectid", how="outer")
        step += 1
        my_bar.progress(step*100 // step_all, text=progress_text)

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

    gdrive_complex_save_file(_service, path_processed, filename, df_historical)

    my_bar.empty()
    st.caption(f'Importing finished. Number of sampling: {len(files_to_import)}')
    return df_historical


# noinspection PyTypeChecker
@st.cache_data
def build_game_db(_service: googleapiclient.discovery.Resource, path_processed: str,
                  df_new: pd.DataFrame):
    if "user_rating" in df_new.columns.values:
        st.caption("Importing detailed game information for user's collection...")
    else:
        st.caption("Importing detailed game information for user's plays...")

    filename_game = "game_infoDB.csv"
    filename_playnum = "playnum_infoDB.csv"

    items = gdrive_search(_service, f'name contains "{filename_game}"')
    if not items:
        df_game_info = pd.DataFrame()
    else:
        previous_game_file_id = items[0]["id"]
        df_game_info = gdrive_load_file(_service, previous_game_file_id)

    items = gdrive_search(_service, f'name contains "{filename_playnum}"')
    if not items:
        df_playnumdb = pd.DataFrame()
    else:
        previous_play_file_id = items[0]["id"]
        df_playnumdb = gdrive_load_file(_service, previous_play_file_id)

    if df_new.empty:
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
        my_bar.progress(step*100 // step_all, text=progress_text)
    my_bar.empty()

    gdrive_complex_save_file(_service, path_processed, filename_game, df_game_info)
    gdrive_complex_save_file(_service, path_processed, filename_playnum, df_playnumdb)

    st.caption(f'Importing finished. {len(games_to_import_list)} new game information saved.')
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


# noinspection PyTypeChecker
@st.cache_data
def import_user_collection(_service: googleapiclient.discovery.Resource, username: str,
                           refresh: int) -> pd.DataFrame:
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
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    st.caption(f'Importing collection of {username}...')
    filename = f'collection_{username}.csv'

    item = gdrive_search(_service, query=f'name contains "{filename}"')
    if item:
        file_id = item[0]["id"]
        df = gdrive_load_file(service=_service, file_name=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of games in collection: {len(df)}')
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

    q = f'mimeType = "application/vnd.google-apps.folder" and name contains "{username}"'
    items = gdrive_search(_service, query=q)
    folder_id = items[0]["id"]
    gdrive_complex_save_file(_service, folder_id, filename, df)

    st.caption(f'Collection imported. Number of games + expansions known: {len(df)}')
    return df


# noinspection PyTypeChecker
@st.cache_data
def import_user_plays(_service: googleapiclient.discovery.Resource, username: str,
                      refresh: int) -> pd.DataFrame:
    """
    Importing all play instances uf a specific user from BGG website
    Has to import for every user separately, so used every time a new user is chosen
    :param _service: Google Drive
    :param username: BGG username
    :param refresh: if the previously imported data is older in days, new import will happen
    :return: imported data in dataframe
    """
    st.caption(f'Importing plays of {username}...')
    df = pd.DataFrame()
    filename = f'plays_{username}.csv'

    item = gdrive_search(_service, query=f'name contains "{filename}"')
    if item:
        file_id = item[0]["id"]
        df = gdrive_load_file(service=_service, file_name=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of plays: {len(df)}')
            return df

    # read the first page of play info from BGG
    result = import_xml_from_bgg(f'plays?username={username}')
    """ BGG returns 100 plays per page
    The top of the XML page stores the number of plays in total
    Here we find this number so we know how many pages to read
    """
    i = result.find("total=")
    total = int("".join(filter(str.isdigit, result[i+7:i+12])))
    if total == 0:
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
    my_bar.progress(step//step_all, text=progress_text)

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

    q = f'mimeType = "application/vnd.google-apps.folder" and name contains "{username}"'
    items = gdrive_search(_service, query=q)
    folder_id = items[0]["id"]
    gdrive_complex_save_file(_service, folder_id, filename, df_play)

    step += 1
    my_bar.progress(step*100 // step_all, text=progress_text)
    my_bar.empty()
    st.caption(f'Importing finished. Number of plays: {len(df_play)}')
    return df_play


def stat_basics(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_info: pd.DataFrame) -> None:
    collection_merged = pd.merge(df_collection, df_game_info, how="left", on="objectid")
    plays_merged = pd.merge(df_plays, df_game_info, how="left", on="objectid")

    collection_all = len(collection_merged)
    collection_games = len(collection_merged.query('type == "boardgame"'))
    collection_exp = len(collection_merged.query('type == "boardgameexpansion"'))
    owned_all = df_collection["own"].loc[df_collection["own"] == 1].count()
    owned_games = len(collection_merged.query('(type == "boardgame") and (own == 1)'))
    owned_exp = len(collection_merged.query('(type == "boardgameexpansion") and (own == 1)'))
    tried_all = df_plays["objectid"].nunique()
    tried_games = plays_merged.query('type == "boardgame"')
    tried_games = tried_games["objectid"].nunique()
    tried_exp = plays_merged.query('type == "boardgameexpansion"')
    tried_exp = tried_exp["objectid"].nunique()
    rated_all = len(collection_merged.query('user_rating > 0'))
    rated_games = len(collection_merged.query('(type == "boardgame") and (user_rating > 0)'))
    rated_exp = len(collection_merged.query('(type == "boardgameexpansion") and (user_rating > 0)'))
    more_all = df_collection["numplays"].loc[df_collection["numplays"] > 1].count()
    more_games = len(collection_merged.query('(type == "boardgame") and (numplays > 1)'))
    more_exp = len(collection_merged.query('(type == "boardgameexpansion") and (numplays > 1)'))
    data = {"Name": ["Size of BGG collection", "Number of items owned", "Number of unique items tried",
                     "Number of items rated by the user", "Played more than once"],
            "Games": [collection_games, owned_games, tried_games, rated_games, more_games],
            "Expansions": [collection_exp, owned_exp, tried_exp, rated_exp, more_exp],
            "All": [collection_all, owned_all, tried_all, rated_all, more_all]}
    df_basic = pd.DataFrame(data, index=pd.RangeIndex(start=1, stop=6, step=1))
    st.dataframe(df_basic, use_container_width=True)

    st.write(f'First play recorded on: {df_plays.date.min()}')
    st.write(f'Number of plays recorded: {df_collection["numplays"].sum()}')
    st.write(f'Mean of plays with a specific game: {df_collection["numplays"].mean():.2f}')
    st.write(f'Median of plays with a specific game: {df_collection["numplays"].median()}')

    with st.expander("See explanation of data"):
        st.write("Data used:")
        st.markdown("- user's collection plays for size of collection, ownership of items, ratings by the user "
                    "(xmlapi2/collection)")
        st.markdown("- user's documented plays for items tried, and other play related statistics (xmlapi2/plays)")
        st.markdown("- Detailed board game info for board game type to separate board games and extensions "
                    "(xmlapi2/thing)")


def stat_favourite_games(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Favourite games")
    st.checkbox('Include boardgame expansions as well', key="h_index_favor")
    df_favourite_games = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_favourite_games = pd.DataFrame(df_favourite_games.loc[df_favourite_games["user_rating"] > 0])
    if "h_index_favor" in st.session_state:
        if not st.session_state.h_index_favor:
            df_favourite_games = df_favourite_games.query('type == "boardgame"')

    df_favourite_games = df_favourite_games.sort_values(by=["user_rating", "numplays", "own"], ascending=False).head(30)
    df_favourite_games = df_favourite_games[['name', 'user_rating', 'yearpublished', 'numplays',  'image', 'objectid']]
    df_favourite_games["objectid"] = df_favourite_games["objectid"].astype("str")
    df_favourite_games.rename(columns={"objectid": "link"}, inplace=True)

    pos = df_favourite_games.columns.get_loc("link")
    for i in range(len(df_favourite_games)):
        df_favourite_games.iloc[i, pos] = f'https://boardgamegeek.com/boardgame/{df_favourite_games.iloc[i, pos]}'

    df_favourite_games.index = pd.RangeIndex(start=1, stop=len(df_favourite_games) + 1, step=1)

    st.dataframe(df_favourite_games, use_container_width=True,
                 column_config={"image": st.column_config.ImageColumn("Image", width="small"),
                                "link": st.column_config.LinkColumn("BGG link", width="small")})


def stat_favourite_designers(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Favourite designers")
    st.selectbox("How to measure?", ("Favourite based on number of games known", "Favourite based on plays",
                                     "Favourite based on user' ratings"), key='sel_designer')

    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df_favourite_designer = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_favourite_designer = df_favourite_designer.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_favourite_designer = df_favourite_designer.query('type == "boardgame"')

    df_favourite_designer = pd.DataFrame(df_favourite_designer[["designer", "name", "numplays",
                                                                "user_rating", "weight"]].reset_index())

    pos = df_favourite_designer.columns.get_loc("designer")
    row_no = len(df_favourite_designer)
    for index in range(row_no):
        designers = str(df_favourite_designer.iloc[index, pos]).split(', ')
        if designers:
            first = designers.pop(0)
            df_favourite_designer.at[index, "designer"] = first
            extra_item = df_favourite_designer.iloc[[index]]
            for one_designer in designers:
                df_favourite_designer = pd.concat([df_favourite_designer, extra_item], ignore_index=True)
                new_pos = len(df_favourite_designer)-1
                df_favourite_designer.at[new_pos, "designer"] = one_designer
    df_favourite_designer = (df_favourite_designer.groupby("designer", sort=False).
                             agg({"index": ["count"], "name": lambda x: ', '.join(set(x)),
                                  "numplays": ["sum"], "user_rating": ["mean"], "weight": ["mean"]}))

    df_favourite_designer = df_favourite_designer.reset_index()
    df_favourite_designer = pd.DataFrame(df_favourite_designer.loc[df_favourite_designer["designer"] != "(Uncredited)"])

    df_favourite_designer.columns = ["Designer", "No of games",  "List of board games known from the designer",
                                     "No of plays", "Average user rating", "Average weight"]

    df_favourite_designer = df_favourite_designer.reset_index()
    if 'sel_designer' not in st.session_state:
        st.session_state.sel_designer = 'Favourite based on number of games known'
    match st.session_state.sel_designer:
        case 'Favourite based on number of games known':
            df_favourite_designer = df_favourite_designer.sort_values("No of games", ascending=False).head(30)
        case 'Favourite based on plays':
            df_favourite_designer = df_favourite_designer.sort_values("No of plays", ascending=False).head(30)
        case "Favourite based on user' ratings":
            df_favourite_designer = df_favourite_designer.sort_values("Average user rating", ascending=False).head(30)

    df_favourite_designer = df_favourite_designer.reset_index()

    row_no = len(df_favourite_designer)
    for i in range(row_no):
        games = df_favourite_designer.at[i, "List of board games known from the designer"]
        games = sorted(str(games).split(', '))
        games = ', '.join(map(str, games))
        df_favourite_designer.at[i, "List of board games known from the designer"] = games

    df_favourite_designer.drop(["index", "level_0"], inplace=True, axis=1)
    df_favourite_designer.index = pd.RangeIndex(start=1, stop=len(df_favourite_designer)+1, step=1)
    st.table(df_favourite_designer)


def stat_not_played(collection: pd.DataFrame) -> None:
    # st.subheader("Owned games not played yet")
    games_owned = collection.loc[collection["own"] == 1]
    not_played = pd.DataFrame(games_owned["name"].loc[games_owned["numplays"] == 0].sort_values())
    if not_played.empty:
        st.write("Congratulation, you have already played with all games you currently own!")
    else:
        not_played.index = pd.RangeIndex(start=1, stop=len(not_played) + 1, step=1)
        st.table(not_played)


def stat_games_by_year(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Games tried grouped by year of publication")
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items of the collection", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")
    cut_year = st.slider('Which year to start from?', 1950, 2020, 2000)

    played = df_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    played = played[["name", "yearpublished", "own", "type", "numplays"]].loc[df_collection["numplays"] != 0].reset_index()
    under_cut = len(played.loc[df_collection["yearpublished"] <= cut_year])
    played["yearpublished"] = played["yearpublished"].clip(lower=cut_year)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            played = played.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            played = played.query('type == "boardgame"')

    played = played.groupby("yearpublished").count().reset_index()
    played.drop(["index", "own", "type", "numplays"], inplace=True, axis=1)
    if under_cut > 0:
        played["yearpublished"] = played["yearpublished"].astype("str")
        played.loc[0, "yearpublished"] = "-" + str(cut_year)
    played.rename(columns={"name": "Quantity"}, inplace=True)
    played.rename(columns={"yearpublished": "Games published that year known"}, inplace=True)

    st.line_chart(played, x="Games published that year known", y="Quantity", height=400)
    with st.expander("Numerical data"):
        played.index = pd.RangeIndex(start=1, stop=len(played) + 1, step=1)
        st.table(played)

    with st.expander("See explanation of data"):
        st.write("Chart represents all items that the user has played with. Sorting the items based on their publication year."
                 " Any games - that was published before the 'starting year' selected - are added to the first year.")
        st.write("Data used:")
        st.markdown("- user's collection for year of publishing, and information whether the item is knows "
                    "for the user (xmlapi2/collection)")
        st.markdown("- Note: technically it is possible that user can have plays documented to an item that is "
                    "not part of his / her collection")
        st.markdown("- Note: BGG does not have publication year info on all items. The missing data is filled with 0.")
        st.markdown("- Detailed board game info for board game type to separate board games and extensions"
                    " (xmlapi2/thing)")


def stat_h_index(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    def count_h(df_raw: pd.DataFrame) -> (pd.DataFrame, int):
        if df_raw.empty:
            return df_raw, 0
        df_count = df_raw.groupby("Name", sort=False).sum().reset_index()
        df_count = df_count.sort_values(by=["Number of plays", "Name"], ascending=[False, True]).reset_index()
        i = 0
        while 0 == 0:
            try:
                if df_count.iloc[i]["Number of plays"] < i + 1:
                    break
            except IndexError:
                break
            i += 1

        df_player_num_votes = pd.DataFrame(df_count[["Name", "Number of plays"]].loc[df_count["Number of plays"] >= i])
        if len(df_player_num_votes) > i:
            extra_text = "Also in the H-index range are: "
            for index in range(i, len(df_player_num_votes)):
                extra_text = (f'{extra_text}{df_player_num_votes.at[index, "Name"]} '
                              f'({df_player_num_votes.at[index, "Number of plays"]} plays), ')
            extra_text = extra_text[:-2]
            df_player_num_votes.at[i, "Name"] = extra_text
            df_player_num_votes["Number of plays"] = df_player_num_votes["Number of plays"].astype(str)
            df_player_num_votes.at[i, "Number of plays"] = f'At least {i}'
            cut = i+1
        else:
            cut = i
        df_player_num_votes.index = pd.RangeIndex(start=1, stop=len(df_player_num_votes) + 1, step=1)
        return df_player_num_votes.head(cut), i

    # st.subheader("H-index")
    st.selectbox("Show data from period...", ('All times', 'Last year (starting from today)',
                                              'For each calendar year'), key='sel_hindex')

    st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df = pd.merge(df_plays, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df = df.query('type == "boardgame"')
    df = df[["name", "quantity", "date"]]
    df.rename(columns={"name": "Name", "quantity": "Number of plays", "date": "Date"}, inplace=True)
    df = df.reset_index()

    if 'sel_hindex' not in st.session_state:
        st.session_state.sel_hindex = 'All times'
    match st.session_state.sel_hindex:
        case 'All times':
            df_result, i = count_h(df)
            st.write(f'H-index is {i}. Games within the H-index:')
            st.table(df_result)
        case 'Last year (starting from today)':
            no_row = len(df)
            one_years_ago = datetime.today() - timedelta(days=365)
            for index in range(no_row):
                play_date = datetime.strptime(df.at[index, "Date"], "%Y-%m-%d")
                if play_date > one_years_ago:
                    df.at[index, "Date"] = 1
                else:
                    df.at[index, "Date"] = 0
            df = df.query(f'Date == 1')
            df_result, i = count_h(df)
            st.write(f'H-index is {i}. Games within the H-index:')
            st.table(df_result)
        case 'For each calendar year':
            df["Date"] = df["Date"].str[0:4].astype(int)
            df = df.sort_values("Date").reset_index(drop=True)
            plays_years = df["Date"].unique().tolist()
            no_row = len(plays_years)
            for index in range(no_row):
                df_yearly = df.query(f'Date == {plays_years[index]}')
                df_result, i = count_h(df_yearly)
                with st.expander(f'For year {plays_years[index]} the H-index is {i}.'):
                    st.table(df_result)

    with st.expander("See explanation of data"):
        st.write("Your h-index is the smallest number of games that you have played at least that number of times.")
        st.write("Data used:")
        st.markdown("- user's documented plays for Name and Number of plays (xmlapi2/plays)")
        st.markdown("- Detailed board game info for board game type to separate board games and extensions"
                    " (xmlapi2/thing)")
    return None


def stat_yearly_plays(df_play_stat: pd.DataFrame) -> None:
    # st.subheader("Play statistics by year")
    # number of new games tried in every year
    df_new_games = df_play_stat.groupby(["name", "objectid"])[["date"]].min()
    df_new_games["year"] = df_new_games["date"].str[0:4].astype(int)
    df_new_games = df_new_games.groupby("year").count()
    df_new_games.rename(columns={"date": "New games tried"}, inplace=True)

    # number of unique games known already at that time
    df_new_games["known_games"] = df_new_games["New games tried"].cumsum()
    df_new_games.rename(columns={"known_games": "Known games"}, inplace=True)

    # number of unique games played in every year
    df_played = df_play_stat
    df_played["year"] = df_played["date"].str[0:4].astype(int)
    df_played = pd.Series(df_played.groupby("year")["objectid"].nunique())
    df_played.rename("Unique games played", inplace=True)

    # number of all plays in every year
    df_all_plays = df_play_stat
    df_all_plays["year"] = df_all_plays["date"].str[0:4].astype(int)
    df_all_plays = df_all_plays.groupby("year")["quantity"].sum()
    df_all_plays.rename("Number of plays", inplace=True)

    df_result = pd.merge(df_new_games, df_played, how="left", on="year")
    df_result = pd.merge(df_result, df_all_plays, how="left", on="year").reset_index()

    st.dataframe(df_result, hide_index=True, use_container_width=True)
    with st.expander("See explanation of data"):
        st.write("Summary of play statistics grouped by year.")
        st.write("Data used:")
        st.markdown("- user's documented plays for Name and Number of plays (xmlapi2/plays)")
        st.write("Description of columns:")
        st.markdown("- New games tried: the number of unique games where the first documented play happened that year")
        st.markdown("- Known games: the number of unique games where the first documented play happened "
                    "UNTIL that year (including that year as well)")
        st.markdown("- Unique games played: the number of unique games where there is at least one documented "
                    "play happened that year")
        st.markdown("- Number of plays: the number of plays documented play happened that year")
        st.write("Note: BGG let you add quantity to a recorded play (like you played that game 3 times in a row, "
                 "and you create one play for all of this. This statistics would count this 3 plays.")
    return None


def stat_historic_ranking(historic: pd.DataFrame, plays: pd. DataFrame) -> None:
    # st.subheader("Games known from BGG top list")
    method = st.selectbox("How to show data?", ('Basic', 'Cumulative'), key='TOP100')
    st.selectbox("Show data from year...", ('2017', '2018', '2019', '2020', '2021'), key='sel_year')
    st.selectbox("Data sampling", ('Yearly', 'Quarterly', 'Monthly'), key='sel_sampling')

    # create list of date we have ranking information
    periods = []
    column_list = historic.columns.values
    for item in column_list:
        if re.match(r'\d{4}-\d{2}-\d{2}', item):
            periods.append(item)

    to_filter = periods
    periods = []
    if 'sel_year' not in st.session_state:
        st.session_state.sel_year = '2017'
    from_year = int(st.session_state.sel_year)
    for item in to_filter:
        this_item = int(item[:4])
        if this_item >= from_year:
            periods.append(item)

    to_filter = periods
    periods = []
    if 'sel_sampling' not in st.session_state:
        st.session_state.sel_sampling = 'Yearly'
    for item in to_filter:
        match st.session_state.sel_sampling:
            case "Yearly":
                this_item = item[-5:]
                if this_item == "01-01":
                    periods.append(item)
            case 'Quarterly':
                this_item = item[-5:]
                if this_item in {"01-01", "04-01", "07-01", "10-01"}:
                    periods.append(item)
            case 'Monthly':
                periods.append(item)

    # create list of games with their first play dates
    df_plays = plays.groupby(["name", "objectid"])[["date"]].min()

    df_result = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300", "top 400", "top 500",
                                      "top1000", "top2000"])
    df_result_cum = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300",
                                          "top 400", "top 500", "top1000", "top2000"])

    for i in range(len(periods)):
        ranking = historic[["objectid", periods[i]]]
        df_known = df_plays[df_plays["date"] <= periods[i]]
        df_known = pd.merge(df_known, ranking, how="left", on="objectid")
        top100 = len(df_known[df_known[periods[i]].between(1, 100)])
        top200 = len(df_known[df_known[periods[i]].between(101, 200)])
        top300 = len(df_known[df_known[periods[i]].between(201, 300)])
        top400 = len(df_known[df_known[periods[i]].between(301, 400)])
        top500 = len(df_known[df_known[periods[i]].between(401, 500)])
        top1000 = len(df_known[df_known[periods[i]].between(501, 1000)])
        top2000 = len(df_known[df_known[periods[i]].between(1001, 2000)])
        df_result.loc[len(df_result)] = [periods[i], top100, top200, top300, top400, top500, top1000, top2000]
        top200 = top200 + top100
        top300 = top300 + top200
        top400 = top400 + top300
        top500 = top500 + top400
        top1000 = top1000 + top500
        top2000 = top2000 + top1000
        df_result_cum.loc[len(df_result_cum)] = [periods[i], top100, top200, top300, top400, top500, top1000, top2000]
    match method:
        case "Basic":
            st.line_chart(df_result, x="Date", height=600)
            st.write("Number of games played from the BGG TOP lists:")
            st.dataframe(df_result, hide_index=True)
        case "Cumulative":
            st.line_chart(df_result_cum, x="Date", height=600)
            st.write("\nNumber of games played from the BGG TOP lists (cumulative):")
            st.dataframe(df_result_cum, hide_index=True)
    return None


def stat_by_weight(df_game_info: pd.DataFrame, df_collection: pd.DataFrame, df_plays: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items played", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    most_played = pd.DataFrame(df_plays.groupby("objectid")["quantity"].sum())
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played = most_played.merge(df_game_info, how="left", on="objectid", suffixes=("", "_y"))
    most_played = most_played.merge(df_collection, how="left", on="objectid", suffixes=("", "_y"))
    most_played["year_published"] = most_played["year_published"].clip(1990)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            most_played = most_played.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            most_played = most_played.query('type == "boardgame"')

    most_played = most_played[["objectid", "type", "name", "year_published", "weight", "quantity", "rating_average"]]
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played.rename(columns={"rating_average": "Average rating on BGG", "weight": "Weight",
                              "quantity": "Number of plays"}, inplace=True)
    fig = px.scatter(most_played, x="Average rating on BGG", y="Weight", size="Number of plays",
                     hover_name="name", height=600
    )
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    with st.expander("See explanation of data"):
        st.write('For each item on BGG there is a number called \'Weight\'. it shows how complex the game is.'
                 'BGG users can rate every item on the website. BGG create multiple average, here the \'Average '
                 'rating\' is used (calculated by BGG). The size of the plots show how many times the user played '
                 'with it.')
        st.markdown("- Note: more serious players prefers games with higher weight. Also more serious players take the "
                    "energy to document plays, maintain a collection and rate games on BGG. As a result, games with "
                    "higher weight usually has higher rating.")
        st.write("Data used:")
        st.markdown("- user's documented plays for Name and Number of plays (xmlapi2/plays)")
        st.markdown("- user's collection for ownership (xmlapi2/collection)")
        st.markdown("- detailed board game info for board game type (to separate board games and "
                    "extensions) (xmlapi2/thing)")
    return None


def stat_by_rating(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items played", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df_rating = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_rating = pd.DataFrame(df_rating.loc[df_rating["user_rating"] > 0])

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_rating = df_rating.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_rating = df_rating.query('type == "boardgame"')

    most_played = pd.DataFrame(df_plays.groupby("objectid").sum())
    df_rating = df_rating.merge(most_played, how="left", left_on="objectid", right_on="index", suffixes=("", "_z"))
    df_rating = df_rating[["name", "numplays", "user_rating", "rating_average"]]
    df_rating.rename(columns={"user_rating": "User's rating", "rating_average": "Average rating on BGG",
                              "numplays": "Number of plays"}, inplace=True)
    df_rating = df_rating.sort_values(by="Number of plays", ascending=False)

    max_size = max(df_rating["Number of plays"].max() // 100, 1)
    df_rating["color_data"] = "Data"
    for i in range(1000):
        new_row = pd.DataFrame({"name": "", "Number of plays": max_size, "User's rating": i/100,
                   "Average rating on BGG": i/100, "color_data": "Equal values line"}, index=[len(df_rating)])
        df_rating = pd.concat([df_rating, new_row])

    fig = px.scatter(df_rating, x="Average rating on BGG", y="User's rating", size="Number of plays",
                     hover_name="name", color="color_data", color_discrete_sequence=["#000000", "#FB0D0D"],
                     size_max=50)
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    with st.expander("See explanation of data"):
        st.write('For each item on BGG users can add rating. BGG create multiple average, here the \'Average '
                 'rating\' is used at axis X (calculated by BGG). The axis Y uses the specific rating of the user.'
                 ' The size of the plots show how many times the user played with it.')
        st.markdown("- Note: players play more with their favourite games. Also they usually rate their favourite"
                    "games higher than the majority of other players. So naturally the plots quite often will be "
                    "to the left of the green points describing this situation.")
        st.write("Data used:")
        st.markdown("- user's documented plays for Name and Number of plays (xmlapi2/plays)")
        st.markdown("- user's collection for ownership (xmlapi2/collection)")
        st.markdown("- detailed board game info for board game type (to separate board games and "
                    "extensions) (xmlapi2/thing)")
    return None


def stat_collection(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame, df_playnum_infodb: pd.DataFrame) -> None:
    def calculate_ideal_player_number():
        row_no = len(df_updated_collection)
        for index in range(row_no):
            feedback = [0, 0, 0, 0, 0, 0, 0, 0]
            object_id = int(df_updated_collection.at[index, "objectid"])
            try:
                min_player = int(df_updated_collection.at[index, "min_player"])
            except ValueError:
                min_player = 0
            try:
                max_player = min(int(df_updated_collection.at[index, "max_player"]), 8)
            except ValueError:
                max_player = 0
            player_info = df_playnum_infodb.query(f'objectid == {object_id}').reset_index()
            inner_row_no = len(player_info)
            if inner_row_no == 0:
                df_updated_collection.at[index, "objectid"] = 0
                df_updated_collection.at[index, "own"] = feedback
                continue
            for j in range(inner_row_no):
                current_playernum = int(player_info.at[j, "numplayers"])
                if min_player <= current_playernum <= max_player:
                    best = int(player_info.at[j, "best"])
                    rec = int(player_info.at[j, "recommended"] * 1)
                    not_rec = int(player_info.at[j, "not recommended"])
                    feedback[current_playernum - 1] = best * 3 + rec + not_rec * 0
                else:
                    continue
            votes = sum(feedback)
            if votes > 0:
                for k in range(8):
                    feedback[k] = (feedback[k] * 100) // votes
            df_updated_collection.at[index, "objectid"] = feedback.index(max(feedback)) + 1
            df_updated_collection.at[index, "own"] = feedback

    # st.subheader("Ideal number of players for each game you own")
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items of the collection", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")
    player_range = st.slider('Narrow on ideal player number', 1, 8, (1, 8), key='stat_playernum')

    df_ordered_collection = df_collection.sort_values("name").reset_index(drop=True)
    df_updated_collection = df_ordered_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_updated_collection = df_updated_collection.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_updated_collection = df_updated_collection.query('type == "boardgame"')
    df_updated_collection.reset_index(drop=True, inplace=True)
    df_updated_collection = df_updated_collection[["name", "numplays", "user_rating", "weight",
                                                   "min_player", "max_player", "objectid",
                                                   "own", "image", "thumbnail"]]
    df_updated_collection["own"] = df_updated_collection["own"].astype(object)

    # create link for the item
    df_updated_collection = pd.DataFrame(df_updated_collection.rename(columns={"thumbnail": "Link"}))
    pos_link = df_updated_collection.columns.get_loc("Link")
    pos_objectid = df_updated_collection.columns.get_loc("objectid")
    for i in range(len(df_updated_collection)):
        df_updated_collection.iloc[i, pos_link] = \
            f'https://boardgamegeek.com/boardgame/{df_updated_collection.iloc[i, pos_objectid]}'

    calculate_ideal_player_number()

    if "stat_playernum" not in st.session_state:
        player_range = (1, 8)
    df_updated_collection["objectid"] = df_updated_collection["objectid"].astype(int)
    df_updated_collection = df_updated_collection.query(f'objectid >= {player_range[0]}')
    df_updated_collection = df_updated_collection.query(f'objectid <= {player_range[1]}')

    df_updated_collection.columns = ["Name", "No plays", "User\'s rating", "Weight", "Min player", "Max player",
                                     "Ideal player no", "BGG votes on player numbers", "Image", "Link"]
    st.dataframe(df_updated_collection, column_config={
        "BGG votes on player numbers": st.column_config.BarChartColumn(
            help="BGG users' feedback on specific player numbers (1-8 players shown)", y_min=0, y_max=100),
        "Image": st.column_config.ImageColumn("Image", width="small"),
        "Weight": st.column_config.NumberColumn(format="%.2f"),
        "Link": st.column_config.LinkColumn("BGG link", width="small")
    }, hide_index=True, use_container_width=True)

    with st.expander("See explanation of data"):
        st.write('Every user has a collection on BGG. A collection "is a virtual collection of games you '
                 'are interested in due to owning them, playing them, rating them, commenting on them, '
                 'wanting to be notified of new content, whatever."')
        st.write("Data used:")
        st.markdown("- user's collection for most of the information about the game, the image and user's "
                    "rating (xmlapi2/collection)")
        st.markdown("- detailed board game info for board game type (to separate board games and "
                    "extensions) and player number information (min, max, votes) (xmlapi2/thing)")
        st.markdown("- ideal player number is calculated from the BGG votes. Calculation for each player "
                    "number: number of 'best' votes	u'*'3 + number of 'recommended' votes u'*'1 + "
                    "number of 'not recommended' votes	u'*'0")
    return None


# noinspection PyTypeChecker
def main():
    # TODO schema for TOP list
    gdrive_original = st.secrets["gdrive_original"]
    gdrive_processed = st.secrets["gdrive_processed"]
    gdrive_user = st.secrets["gdrive_user"]
    REFRESH_USER_DATA = 3  # for importing user data - number represents days

    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state, layout="wide")

    my_service = gdrive_authenticate()

    if "user_exist" not in st.session_state:
        st.session_state.user_exist = False

    with st.sidebar:
        st.title("BGG statistics")

        with st.form("my_form"):
            bgg_username = st.text_input('Enter a BGG username', key="input_username")
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.stat_selection = "Basic statistics"
                st.session_state.user_exist = check_bgg_user(my_service, bgg_username, gdrive_user)
                if (not st.session_state.user_exist) and ('handler' in st.session_state):
                    del st.session_state["handler"]

        st.caption("User data is cached for 3 days. Push the button if you want to have fresh data")
        if st.button(label="Refresh selected user's data"):
            import_user_collection(my_service, bgg_username, 0)
            import_user_plays(my_service, bgg_username, 0)

        if submitted:
            st.session_state.stat_selection = "Basic statistics"
            st.session_state.user_exist = check_bgg_user(my_service, bgg_username, gdrive_user)
            if (not st.session_state.user_exist) and ('handler' in st.session_state):
                del st.session_state["handler"]

        if st.session_state.user_exist:
            placeholder = st.empty()
            with placeholder.container():
                st.subheader("Importing...")
                # my_: data that is user specific
                my_collection = import_user_collection(my_service, bgg_username, REFRESH_USER_DATA)
                my_plays = import_user_plays(my_service, bgg_username, REFRESH_USER_DATA)
                # global_: data independent from user
                build_game_db(my_service, gdrive_processed, my_collection)
                global_game_infodb, global_playnumdb = build_game_db(my_service, gdrive_processed, my_plays)
                global_fresh_ranking = import_current_ranking(my_service, gdrive_processed)
                global_historic_rankings = import_historic_ranking(my_service, gdrive_original, gdrive_processed,
                                                                   global_fresh_ranking)
                st.write("IMPORTING / LOADING has finished!\n")
            placeholder.empty()

    if st.session_state.user_exist:
        if not (my_collection.empty or my_plays.empty):
            # user has enough information to present statistics
            st.title(f'Statistics of {bgg_username}')
            option = st.selectbox('Choose a statistic',
                                  ('Basic statistics', 'User\'s collection', 'Favourites',
                                   'H-index', 'Games tried grouped by year of publication',
                                   'Play statistics by year', 'Games known from BGG top list',
                                   'Stat around game weight', 'Stat around ratings'), key='stat_selection')
            match option:
                case "Basic statistics":
                    stat_basics(my_collection, my_plays, global_game_infodb)
                    # stat_not_played(my_collection)
                case "User\'s collection":
                    stat_collection(my_collection, global_game_infodb, global_playnumdb)
                case "Favourites":
                    opt_fav = st.selectbox('Choose a topic', ('Favourite games', 'Favourites Designers'),
                                           key='stat_fav')
                    match opt_fav:
                        case 'Favourite games':
                            stat_favourite_games(my_collection, global_game_infodb)
                        case 'Favourites Designers':
                            stat_favourite_designers(my_collection, global_game_infodb)
                case "H-index":
                    stat_h_index(my_plays, global_game_infodb)
                case "Games tried grouped by year of publication":
                    stat_games_by_year(my_collection, global_game_infodb)
                case "Play statistics by year":
                    stat_yearly_plays(my_plays)
                case "Games known from BGG top list":
                    stat_historic_ranking(global_historic_rankings, my_plays)
                case "Stat around game weight":
                    stat_by_weight(global_game_infodb, my_collection, my_plays)
                case "Stat around ratings":
                    stat_by_rating(my_collection, my_plays, global_game_infodb)
        else:
            # user exists but no information
            st.title("Statistics")
            st.write("The selected user has not enough information to show statistics. Enter a user name first!")
    else:
        # no valid user selected
        st.title("Statistics")
        st.write("Enter a user name first!")
        st.write("Use the sidebar on the left! Click the tiny arrow in the top left corner to open it.")


if __name__ == "__main__":
    main()
