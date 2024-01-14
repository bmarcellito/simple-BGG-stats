import pandas as pd

from my_gdrive.search import file_search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from my_logger import log_info, log_error


def import_current_ranking(df_current_ranking: pd.DataFrame) -> pd.DataFrame:
    """
    There is no API on BGG for downloading all games and their current rankings
    However they upload a .csv file daily that has all the information - as a part of official API
    This function reads such a file once it is uploaded manually to the origin folder
    :param df_current_ranking: existing dataset in memory
    :return: imported data in dataframe
    """
    q = f'"folder_original" in parents and name contains "current_ranking_source"'
    try:
        items_source = file_search(query=q)
    except ValueError:
        items_source = None
    if not items_source:
        data_source = False
        source_last_modified = 0
    else:
        data_source = True
        source_last_modified = items_source[0]["modifiedTime"]

    q = f'"folder_processed" in parents and name contains "current_ranking_processed"'
    try:
        items_processed = file_search(query=q)
    except ValueError:
        items_processed = None
    if not items_processed:
        data_processed = False
        process_last_modified = 0
    else:
        data_processed = True
        process_last_modified = items_processed[0]["modifiedTime"]

    if (not data_source) and (not data_processed):
        log_error(f'import_current_ranking - Current ranking info: No original & no processed data!')
        return pd.DataFrame()

    if (not data_source) and data_processed:
        # initial loading already loaded it.
        return df_current_ranking

    if data_source and data_processed:
        if process_last_modified > source_last_modified:
            # initial loading already loaded it.
            return df_current_ranking

    try:
        df = load_zip(file_id=items_source[0]["id"])
    except ValueError:
        return df_current_ranking
    df = df[["id", "name", "yearpublished", "rank", "abstracts_rank", "cgs_rank", "childrensgames_rank",
             "familygames_rank", "partygames_rank", "strategygames_rank", "thematic_rank", "wargames_rank"]]
    df.rename(columns={"id": "objectid"}, inplace=True)

    overwrite_background(parent_folder="folder_processed", filename="current_ranking_processed", df=df)
    log_info(f'Found new current ranking data. It is imported. Number of items: {len(df)}')
    return df
