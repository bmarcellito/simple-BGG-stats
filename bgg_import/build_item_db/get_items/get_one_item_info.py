from io import StringIO
import pandas as pd

from bgg_import.build_item_db.get_items.get_player_number import import_player_number
from my_logger import log_error


def get_one_item_info(i, xml_text: str) -> (pd.DataFrame, pd.DataFrame, bool):
    result = xml_text
    row_objectid = i
    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8")
    except ValueError:
        log_error(f'get_one_item_info - Objectid: {i}. User has related record, however BGG miss this item!')
        return pd.DataFrame(), pd.DataFrame(), False
    except Exception as e:
        log_error(f'get_one_item_info - Objectid: {i}. XML reading error in "get_one_item_info" function. {e}')
        return pd.DataFrame(), pd.DataFrame(), True
    row_type = df_item.iloc[0, 0]
    if row_type not in ("boardgame", "boardgameexpansion"):
        # this item is not a board game or expansion (BGG has video games and RPG related items as well)
        return pd.DataFrame(), pd.DataFrame(), False
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
        log_error(f'get_one_item_info - Objectid: {i} has no yearpublished info')
        row_published = 0

    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//minplayers")
        row_min_player = df_item.iloc[0, 0]
    except ValueError:
        log_error(f'get_one_item_info - Objectid: {i} has no minplayers info')
        row_min_player = 0

    try:
        df_item = pd.read_xml(StringIO(result), encoding="utf-8", xpath=".//maxplayers")
        row_max_player = df_item.iloc[0, 0]
    except ValueError:
        log_error(f'get_one_item_info - Objectid: {i} has no maxplayers info')
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
    return new_row, df_playnum, False
