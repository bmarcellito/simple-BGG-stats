import re
import pandas as pd

from my_gdrive.load_functions import load_zip
from my_gdrive.save_functions import overwrite_background
from my_gdrive.search import search
from my_logger import log_info, log_error


def import_historic_ranking(current_historic_ranking: pd.DataFrame) -> pd.DataFrame:
    """
    Historic game ranking information cannot be accessed via API at BGG
    There are scrape files available for every day since 2016. Filename convention: YYYY-MM-DD.csv
    This function loads the uploaded files from the original folder and add the ranking information as a new column
    :param current_historic_ranking: current data available in the memory
    :return: imported data in dataframe
    """
    def sort_files(sort_by):
        return sort_by["name"]

    # TODO: games with multiple ID issue
    if len(current_historic_ranking) > 0:
        df_historical = current_historic_ranking
        existing_imports = df_historical.columns.values.tolist()
    else:
        df_historical = pd.DataFrame(columns=["objectid", "best_rank"])
        existing_imports = []

    # identifying the historical data files
    files_to_import = []
    items = search(query=f'"folder_original" in parents')
    if not items:
        # log_info(f'Processed Historical rankings loaded. No historical original data found')
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
            log_error("import_current_ranking - No game info list available, no processed historical game "
                      "rankings available.")
        # else:
        #     log_info(f'Historical ranking loaded. No new data')
        return df_historical

    # each iteration loads a file, and adds the ranking information from it as a column to the historical dataframe
    for step, i in enumerate(files_to_import):
        historical_loaded = load_zip(file_id=i["id"])
        historical_loaded = historical_loaded[["ID", "Rank"]]
        column_name = i["name"]
        name_len = len(column_name)
        column_name = column_name[:name_len - 4]
        historical_loaded.rename(columns={"Rank": column_name}, inplace=True)
        historical_loaded.rename(columns={"ID": "objectid"}, inplace=True)
        df_historical = df_historical.merge(historical_loaded, on="objectid", how="outer")

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

    overwrite_background(parent_folder="folder_processed", filename="historical_ranking_processed", df=df_historical)
    log_info(f'Found new hist historical rankings info. Imported successfully.')
    return df_historical
