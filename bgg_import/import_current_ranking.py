import pandas as pd

from my_gdrive.search import search
from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from my_logger import timeit, logger


@timeit
def import_current_ranking(df_current_ranking: pd.DataFrame) -> pd.DataFrame:
    """
    There is no API on BGG for downloading all games and their current rankings
    However they upload a .csv file daily that has all the information - as a part of official API
    This function reads such a file once it is uploaded manually to the origin folder
    :param df_current_ranking: existing dataset in memory
    :return: imported data in dataframe
    """
    q = f'"folder_original" in parents and name contains "current_ranking_source"'
    items_source = search(query=q)
    if not items_source:
        source_last_modified = 0
        data_source = False
    else:
        source_last_modified = items_source[0]["modifiedTime"]
        data_source = True

    q = f'"folder_processed" in parents and name contains "current_ranking_processed"'
    items_processed = search(query=q)
    if not items_processed:
        data_processed = False
        process_last_modified = 0
    else:
        data_processed = True
        process_last_modified = items_processed[0]["modifiedTime"]

    if (not data_source) and (not data_processed):
        logger.error(f'Current ranking info: No original & no processed data!')
        return pd.DataFrame()

    if (not data_source) and data_processed:
        # initial loading already loaded it.
        return df_current_ranking

    if data_source and data_processed:
        if process_last_modified > source_last_modified:
            # initial loading already loaded it.
            return df_current_ranking

    df = load_zip(file_id=items_source[0]["id"])
    df = df[["id", "name", "yearpublished", "rank", "abstracts_rank", "cgs_rank", "childrensgames_rank",
             "familygames_rank", "partygames_rank", "strategygames_rank", "thematic_rank", "wargames_rank"]]
    df.rename(columns={"id": "objectid"}, inplace=True)

    overwrite_background(parent_folder="folder_processed", filename="current_ranking_processed", df=df)
    logger.info(f'Found new current ranking data. It is imported. Number of items: {len(df)}')
    return df
