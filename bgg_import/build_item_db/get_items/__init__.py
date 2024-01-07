import pandas as pd
import streamlit as st

from bgg_import.build_item_db.get_items.get_one_item_info import get_one_item_info
from bgg_import.import_xml_from_bgg import import_xml_from_bgg
from my_logger import log_error


def get_100_items(games_to_import_list: list, global_game_infodb: pd.DataFrame, global_play_numdb: pd.DataFrame) \
        -> (pd.DataFrame, pd.DataFrame, bool):
    list_of_games = ",".join(str(x) for x in games_to_import_list)
    result = import_xml_from_bgg(f'thing?id={list_of_games}&stats=1')
    if result == "":
        return pd.DataFrame, pd.DataFrame, True
    xml_list = result.split("</item>")
    for i in range(1, len(xml_list)):
        xml_list[i] = '<?xml version="1.0" encoding="utf-8"?><items>' + xml_list[i] + "</item></items>"
        # <items termsofuse="https://boardgamegeek.com/xmlapi/termsofuse">
    xml_list[0] = xml_list[0] + "</item></items>"

    df_game_info = pd.DataFrame()
    df_playnumdb = pd.DataFrame()
    sum_error = False
    progress_text = "Reading game information..."
    my_bar = st.progress(0, text=progress_text)
    step_all = len(games_to_import_list)
    for step, i in enumerate(games_to_import_list):
        new_item_row, new_playnum_rows, error = get_one_item_info(i, xml_list[step])
        sum_error = sum_error and error
        if len(new_item_row) > 0:
            if df_game_info.empty:
                df_game_info = pd.DataFrame(new_item_row, index=[0])
            else:
                try:
                    df_game_info.loc[len(df_game_info)] = new_item_row
                except ValueError:
                    log_error(f'get_100_items - item_id: {i}. It has different attributes, cannot add to table! '
                              f'Columns: {df_game_info.columns.values}')
                    exit(0)
        if len(new_playnum_rows) > 0:
            if df_playnumdb.empty:
                df_playnumdb = pd.DataFrame(new_playnum_rows, index=[0])
            else:
                df_playnumdb = pd.concat([df_playnumdb, new_playnum_rows], ignore_index=True)
        my_bar.progress((step+1) * 100 // step_all, text=progress_text)

    my_bar.empty()
    df_game_info = pd.concat([global_game_infodb, df_game_info], ignore_index=True)
    df_game_info.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True, inplace=True)
    df_playnumdb = pd.concat([global_play_numdb, df_playnumdb], ignore_index=True)
    df_playnumdb.drop_duplicates(subset=["objectid", "numplayers"], keep="last", ignore_index=True, inplace=True)

    st.caption(f'Importing finished. {len(games_to_import_list)} new item information saved.')
    return df_game_info, df_playnumdb, sum_error
