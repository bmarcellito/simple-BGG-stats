import requests  # reading websites
import time
from io import StringIO

# dataframes
import pandas as pd

# reading historical scraped files
from datetime import datetime

# WEB interface
import streamlit as st
import plotly as px

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
    service_account_file = 'service_account.json'
    creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
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
    df.to_csv(buffer, sep=",", index=False, mode="wb", encoding="UTF-8")
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='text / csv')
    file = service.files().create(body=file_metadata, media_body=media_content, fields="id").execute()
    file_id = file.get("id")
    return file_id


def gdrive_overwrite_file(service: googleapiclient.discovery.Resource, file_name: str, df: pd.DataFrame) -> None:
    buffer = io.BytesIO()
    df.to_csv(buffer, sep=",", index=False, mode="wb", encoding="UTF-8")
    buffer.seek(0)
    media_content = MediaIoBaseUpload(buffer, mimetype='text / csv')
    service.files().update(fileId=file_name, media_body=media_content).execute()
    return None


def gdrive_delete_file(service: googleapiclient.discovery.Resource, file_id: str) -> None:
    service.files().delete(fileId=file_id).execute()
    return None


def gdrive_search(service: googleapiclient.discovery.Resource, query: str):
    results = service.files().list(q=query, fields='files(id, name, modifiedTime)').execute()
    return results.get('files', [])


def gdrive_load_file(service, file_name: str) -> pd.DataFrame:
    try:
        request = service.files().get_media(fileId=file_name)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(f"Download {int(status.progress() * 100)}.")
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

    items_source = gdrive_search(_service, "name contains 'boardgames_ranks.csv'")
    if not items_source:
        print("No source file")
        source_last_modified = 0
        data_source = False
    else:
        source_last_modified = items_source[0]["modifiedTime"]
        data_source = True

    items_processed = gdrive_search(_service, "name contains 'current_ranking.csv'")
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
    df.rename(columns={"id": "ID"}, inplace=True)
    if data_processed:
        gdrive_overwrite_file(_service, file_name=items_processed[0]["id"], df=df)
    else:
        gdrive_save_file(_service, parent_folder=path_processed, file_name="current_ranking.csv", df=df)
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

    items = gdrive_search(_service, 'name contains "historical_ranking.csv"')
    if not items:
        print('No processed historic ranking file found.')
        existing_imports = []
        # game DB is the start of the historical dataframe
        df_historical = game_list[["ID", "name", "yearpublished"]].set_index("ID")
        previous_file_exists = False
    else:
        df_historical = gdrive_load_file(_service, items[0]["id"])
        existing_imports = df_historical.columns.values.tolist()
        del existing_imports[:3]
        previous_file_exists = True
        previous_file_id = items[0]["id"]

    # identifying the historical data files
    files_to_import = []
    q = f'"{path_source}" in parents'
    items = gdrive_search(_service, query=q)
    if not items:
        print('No historic ranking files found.')
        return df_historical

    for item in items:
        if re.match(r'\d{4}-\d{2}-\d{2}', item['name']):
            if not (item["name"] in existing_imports):
                files_to_import.append(item)

    files_to_import.sort(key=sort_files)

    if not files_to_import:
        st.caption(f'Importing finished. Number of sampling: {len(existing_imports)}')
        return df_historical

    # each iteration loads a file, and adds the ranking information from it as a column to the historical dataframe
    progress_text = "Importing new historical game rankings file..."
    step_all = len(files_to_import)+1
    step = 0
    my_bar = st.progress(0, text=progress_text)
    for i in files_to_import:
        historical_loaded = gdrive_load_file(_service, i["id"])
        historical_loaded = historical_loaded[["ID", "Rank"]]
        historical_loaded.rename(columns={"Rank": i["name"]}, inplace=True)
        df_historical = df_historical.merge(historical_loaded, on="ID", how="outer")
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

    if previous_file_exists:
        gdrive_overwrite_file(_service, file_name=previous_file_id, df=df_historical)
    else:
        gdrive_save_file(_service, parent_folder=path_processed, file_name="historical_ranking.csv", df=df_historical)

    my_bar.empty()
    st.caption(f'Importing finished. Number of sampling: {len(files_to_import)}')
    return df_historical


def build_game_db(_service: googleapiclient.discovery.Resource, path_processed: str,
                  df: pd.DataFrame) -> pd.DataFrame:
    st.caption("Importing detailed game information...")

    items = gdrive_search(_service, "name contains 'game_infoDB.csv'")
    if not items:
        previous_file_exists = False
        df_game_info = pd.DataFrame()
    else:
        previous_file_exists = True
        previous_file_id = items[0]["id"]
        df_game_info = gdrive_load_file(_service, previous_file_id)

    unique_games = df.groupby("objectid").count().reset_index()
    unique = unique_games["objectid"].tolist()

    games_to_dl = []
    if not df_game_info.empty:
        for i in unique:
            if i not in df_game_info["objectid"].values:
                games_to_dl.append(i)
    else:
        games_to_dl = unique

    progress_text = "Reading game information..."
    my_bar = st.progress(0, text=progress_text)
    step = 0
    step_all = len(games_to_dl)
    for i in games_to_dl:
        result = import_xml_from_bgg(f'thing?id={i}&stats=1')
        row_objectid = i

        df = pd.read_xml(StringIO(result), encoding="utf-8")
        row_type = df.iloc[0, 0]
        if "thumbnail" in df:
            row_thumbnail = df.iloc[0, 2]
        else:
            row_thumbnail = ""
        if "image" in df:
            row_image = df.iloc[0, 3]
        else:
            row_image = ""

        df = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//yearpublished")
        row_published = df.iloc[0, 0]

        df = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//minplayers")
        row_min_player = df.iloc[0, 0]

        df = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//maxplayers")
        row_max_player = df.iloc[0, 0]

        df = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//name")
        df = df.query('type == "primary"')
        row_name = df.iloc[0, 2]

        game_links = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//link")
        df = game_links.query('type == "boardgamedesigner"')
        row_designer = ', '.join(df["value"])

        if "inbound" in game_links:
            df = game_links.query('(type == "boardgameexpansion") and (inbound == "false")')
            row_expansion_of = ', '.join(df["value"])
        else:
            df = game_links.query('type == "boardgameexpansion"')
            row_expansion_of = ', '.join(df["value"])

        if "inbound" in game_links:
            df = game_links.query('(type == "boardgameexpansion") and (inbound == "true")')
            row_expansion_for = ', '.join(df["value"])
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
        my_bar.progress(step*100 // step_all, text=progress_text)
    my_bar.empty()

    if previous_file_exists:
        gdrive_overwrite_file(_service, file_name=previous_file_id, df=df_game_info)
    else:
        gdrive_save_file(_service, parent_folder=path_processed, file_name="game_infoDB.csv", df=df_game_info)

    st.caption(f'Importing finished. {len(games_to_dl)} new game information saved.')
    return df_game_info


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

    q = f'name contains "collection_{username}"'
    item = gdrive_search(_service, query=q)
    if item:
        processed_file = True
        file_id = item[0]["id"]
        df = gdrive_load_file(service=_service, file_name=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of games in collection: {len(df)}')
            print(f'Collection is {how_fresh.days} days old.')
            return df
    else:
        processed_file = False

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
    df_rating = df_rating.fillna(-1)
    df_rating.rename(columns={"value": "user_rating"}, inplace=True)
    df = pd.concat([df, df_rating], axis=1).reset_index(drop=True)

    # User information related to the games, like owned, ...
    df_status = pd.read_xml(StringIO(result), xpath=".//status")
    df = pd.concat([df, df_status], axis=1).reset_index(drop=True)

    df = df.sort_values("yearpublished").reset_index()

    if processed_file:
        q = f'mimeType = "text / csv" and name contains "collection_{username}"'
        items = gdrive_search(_service, query=q)
        file_id = items[0]["id"]
        gdrive_overwrite_file(service=_service, file_name=file_id, df=df)
    else:
        q = f'mimeType = "application/vnd.google-apps.folder" and name contains "{username}"'
        items = gdrive_search(_service, query=q)
        folder_id = items[0]["id"]
        file_name = f'collection_{username}.csv'
        gdrive_save_file(service=_service, parent_folder=folder_id, file_name=file_name, df=df)
    st.caption(f'Collection imported. Number of games + expansions known: {len(df)}')
    return df


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

    q = f'name contains "plays_{username}"'
    item = gdrive_search(_service, query=q)
    if item:
        processed_file = True
        file_id = item[0]["id"]
        df = gdrive_load_file(service=_service, file_name=file_id)
        last_imported = item[0]["modifiedTime"]
        last_imported = datetime.strptime(last_imported, "%Y-%m-%dT%H:%M:%S.%fZ")
        how_fresh = datetime.now() - last_imported
        if how_fresh.days < refresh:
            st.caption(f'Importing finished. Number of plays: {len(df)}')
            print(f'Collection is {how_fresh.days} days old.')
            return df
    else:
        processed_file = False

    # read the first page of play info from BGG
    result = import_xml_from_bgg(f'plays?username={username}')
    """ BGG returns 100 plays per page
    The top of the XML page stores the number of plays in total
    Here we find this number so we know how many pages to read
    """
    i = result.find("total=")
    page_no, rest = divmod(int("".join(filter(str.isdigit, result[i+7:i+12]))), 100)
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

    if processed_file:
        q = f'mimeType = "text / csv" and name contains "plays_{username}"'
        items = gdrive_search(_service, query=q)
        file_id = items[0]["id"]
        gdrive_overwrite_file(service=_service, file_name=file_id, df=df_play)
    else:
        q = f'mimeType = "application/vnd.google-apps.folder" and name contains "{username}"'
        items = gdrive_search(_service, query=q)
        folder_id = items[0]["id"]
        file_name = f'plays_{username}.csv'
        gdrive_save_file(service=_service, parent_folder=folder_id, file_name=file_name, df=df_play)

    step += 1
    my_bar.progress(step*100 // step_all, text=progress_text)
    my_bar.empty()
    st.caption(f'Importing finished. Number of plays: {len(df_play)}')
    return df_play


def stat_basics(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_info: pd.DataFrame) -> None:
    collection_merged = pd.merge(df_collection, df_game_info, how="left", on="objectid")
    plays_merged = pd.merge(df_plays, df_game_info, how="left", on="objectid")

    owned_all = df_collection["own"].loc[df_collection["own"] == 1].count()
    owned_games = len(collection_merged.query('(type == "boardgame") and (own == 1)'))
    owned_exp = len(collection_merged.query('(type == "boardgameexpansion") and (own == 1)'))
    tried_all = df_plays["objectid"].nunique()
    tried_games = plays_merged.query('type == "boardgame"')
    tried_games = tried_games["objectid"].nunique()
    tried_exp = plays_merged.query('type == "boardgameexpansion"')
    tried_exp = tried_exp["objectid"].nunique()
    more_all = df_collection["numplays"].loc[df_collection["numplays"] > 1].count()
    more_games = len(collection_merged.query('(type == "boardgame") and (numplays > 1)'))
    more_exp = len(collection_merged.query('(type == "boardgameexpansion") and (numplays > 1)'))
    data = {"Name": ["Number of games owned", "Number of unique games tried", "Games played more than once"],
            "Games": [owned_games, tried_games, more_games],
            "Expansions": [owned_exp, tried_exp, more_exp],
            "All": [owned_all, tried_all, more_all]}
    df_basic = pd.DataFrame(data, index=pd.RangeIndex(start=1, stop=4, step=1))
    st.write(df_basic)

    st.write(f'First play recorded on: {df_plays.date.min()}')
    st.write(f'Number of plays recorded: {df_collection["numplays"].sum()}')
    st.write(f'Mean of plays with a specific game: {df_collection["numplays"].mean():.2f}')
    st.write(f'Median of plays with a specific game: {df_collection["numplays"].median()}')


def stat_not_played(collection: pd.DataFrame) -> None:
    # st.subheader("Owned games not played yet")
    games_owned = collection.loc[collection["own"] == 1]
    not_played = pd.DataFrame(games_owned["name"].loc[games_owned["numplays"] == 0].sort_values())
    if len(not_played) == 0:
        st.write("Congratulation, you have already played with all games you currently own!")
    else:
        not_played.index = pd.RangeIndex(start=1, stop=len(not_played) + 1, step=1)
        st.table(not_played)


def stat_games_by_year(df_collection: pd.DataFrame, cut: int) -> None:
    st.subheader("Games tried grouped by year of publication")
    played = df_collection[["name", "yearpublished"]].loc[df_collection["numplays"] != 0].reset_index()
    under_cut = len(played.loc[df_collection["yearpublished"] <= cut])
    played["yearpublished"] = played["yearpublished"].clip(lower=cut)
    played = played.groupby("yearpublished").count().reset_index()
    played.drop("index", inplace=True, axis=1)
    if under_cut > 0:
        played["yearpublished"] = played["yearpublished"].astype("str")
        played.loc[0, "yearpublished"] = "Till " + str(cut)
    st.dataframe(played, hide_index=True)


def stat_h_index(df_collection: pd.DataFrame, df_game_info: pd.DataFrame) -> None:
    # st.subheader("H-index")
    st.checkbox('Include boardgame expansions as well', key="h_index_exp")
    df_collection = pd.merge(df_collection, df_game_info, how="left", on="objectid", suffixes=("", "_y"))
    df_collection = df_collection.sort_values(by="numplays", ascending=False).reset_index()
    if "h_index_exp" in st.session_state:
        if not st.session_state.h_index_exp:
            df_collection = df_collection.query('type == "boardgame"')
    i = 0
    while 0 == 0:
        if df_collection.iloc[i]["numplays"] < i+1:
            break
        i += 1
    df_result = pd.DataFrame(df_collection[["name", "numplays"]].loc[df_collection["numplays"] >= i])
    df_result.index = pd.RangeIndex(start=1, stop=len(df_result)+1, step=1)
    st.write(f'H-index is {i}. Games within the H-index:')
    st.table(df_result.head(i))
    return None


def stat_yearly_plays(df_play_stat: pd.DataFrame) -> None:
    # st.subheader("Play statistics by year")
    # number of new games tried in every year
    df_new_games = df_play_stat.groupby(["name", "objectid"])[["date"]].min()
    df_new_games["year"] = df_new_games["date"].str[0:4].astype(int)
    df_new_games = df_new_games.groupby("year").count()
    df_new_games.rename(columns={"date": "new_games_tried"}, inplace=True)

    # number of unique games known already at that time
    df_new_games["known_games"] = df_new_games["new_games_tried"].cumsum()

    # number of unique games played in every year
    df_played = df_play_stat
    df_played["year"] = df_played["date"].str[0:4].astype(int)
    df_played = pd.Series(df_played.groupby("year")["objectid"].nunique())
    df_played.rename("unique_games_played", inplace=True)

    # number of all plays in every year
    df_all_plays = df_play_stat
    df_all_plays["year"] = df_all_plays["date"].str[0:4].astype(int)
    df_all_plays = df_all_plays.groupby("year")["quantity"].sum()
    df_all_plays.rename("no_plays", inplace=True)

    df = pd.merge(df_new_games, df_played, how="left", on="year")
    df = pd.merge(df, df_all_plays, how="left", on="year").reset_index()
    st.dataframe(df, hide_index=True)
    return None


def stat_historic_ranking(historic: pd.DataFrame, plays: pd. DataFrame) -> None:
    # st.subheader("Games known from BGG top list")
    method = st.selectbox("How to show data?", ('Basic (table format)', 'Basic (chart)',
                                                'Cumulative (table format)', 'Cumulative (chart)'), key='TOP100')

    # create list of date we have ranking information
    periods = pd.DataFrame(historic.columns).tail(-4).iloc[:, 0].values.tolist()

    # create list of games with their first play dates
    df_plays = plays.groupby(["name", "objectid"])[["date"]].min()

    df_result = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300", "top 400", "top 500",
                                      "top1000", "top2000"])
    df_result_cum = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300",
                                          "top 400", "top 500", "top1000", "top2000"])

    for i in range(len(periods)):
        ranking = historic[["ID", periods[i]]]
        df_known = df_plays[df_plays["date"] <= periods[i]]
        df_known = pd.merge(df_known, ranking, how="left", left_on="objectid", right_on="ID")
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
    table_height = (len(df_result)+1) * 35 + 3
    match method:
        case "Basic (table format)":
            st.write("Number of games played from the BGG TOP lists:")
            st.dataframe(df_result, hide_index=True, height=table_height)
        case "Basic (chart)":
            st.line_chart(df_result, x="Date")
        case "Cumulative (table format)":
            st.write("\nNumber of games played from the BGG TOP lists (cumulative):")
            st.dataframe(df_result_cum, hide_index=True, height=table_height)
        case "Cumulative (chart)":
            st.line_chart(df_result_cum, x="Date")
    return None


def stat_by_weight(df_game_info: pd.DataFrame, df_plays: pd.DataFrame) -> None:
    st.checkbox('Include boardgame expansions as well', key="weight_exp")
    most_played = pd.DataFrame(df_plays.groupby("objectid")["quantity"].sum())
    most_played = most_played.sort_values("quantity", ascending=False).head(100)
    most_played = pd.merge(most_played, df_game_info, how="left", on="objectid")
    most_played["year_published"] = most_played["year_published"].clip(1990)
    most_played = (most_played[["objectid", "type", "name", "year_published", "weight", "quantity", "rating_average"]].
                   sort_values("quantity", ascending=False))
    if "weight_exp" in st.session_state:
        if not st.session_state.weight_exp:
            most_played = most_played.query('type == "boardgame"')
    fig = px.scatter(
        most_played,
        x="rating_average",
        y="weight",
        size="quantity", hover_data="name", height=600
    )
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)


# noinspection PyTypeChecker
def main():
    # TODO schema for TOP list
    # TODO boardgame vs extension + complexity
    download_in_days = 3  # for importing user data
    year_cut = 2000  # for stat_games_by_year function

    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    st.set_page_config(initial_sidebar_state=st.session_state.sidebar_state)

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
                my_collection = import_user_collection(my_service, bgg_username, download_in_days)
                my_plays = import_user_plays(my_service, bgg_username, download_in_days)
                # global_: data independent from user
                build_game_db(my_service, processed_path, my_collection)
                global_game_info = build_game_db(my_service, processed_path, my_plays)
                global_fresh_ranking = import_current_ranking(my_service, gdrive_processed)
                global_historic_rankings = import_historic_ranking(my_service, gdrive_original, gdrive_processed,
                                                                   global_fresh_ranking)
                st.write("IMPORTING / LOADING has finished!\n")
            placeholder.empty()

    if st.session_state.user_exist:
        st.title(f'Statistics of {bgg_username}')
        option = st.selectbox('Choose a statistic',
                              ('Basic statistics', 'Games tried grouped by year of publication',
                               'H-index', 'Owned games not played yet', 'Play statistics by year',
                               'Games known from BGG top list', 'Stat around game weight'),
                              key='stat_selection')
        match option:
            case "Basic statistics":
                stat_basics(my_collection, my_plays, global_game_info)
            case "Owned games not played yet":
                stat_not_played(my_collection)
            case "Games tried grouped by year of publication":
                stat_games_by_year(my_collection, year_cut)
            case "H-index":
                stat_h_index(my_collection, global_game_info)
            case "Play statistics by year":
                stat_yearly_plays(my_plays)
            case "Games known from BGG top list":
                stat_historic_ranking(global_historic_rankings, my_plays)
            case "Stat around game weight":
                stat_by_weight(global_game_info, my_plays)
    else:
        st.title("Statistics")
        st.write("Enter a user name first!")

        if 'handler' not in st.session_state:
            st.session_state.handler = 2
        if st.session_state.handler == 2:
            st.session_state.sidebar_state = "collapsed"
            st.session_state.handler = 1
            time.sleep(.1)
            st.rerun()
        if st.session_state.handler == 1:
            st.session_state.sidebar_state = "expanded"
            st.session_state.handler = 0
            time.sleep(.1)
            st.rerun()


if __name__ == "__main__":
    main()
