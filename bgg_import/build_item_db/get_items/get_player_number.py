from xml.etree import ElementTree as ET

import pandas as pd


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
