import pandas as pd
import datetime


def calculate_games_by_publication_year(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_owned: bool,
                                        toggle_collection: bool, cut_year: int) -> pd.DataFrame:
    if len(df_collection) == 0:
        return pd.DataFrame()
    played = df_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    played = (played[["name", "yearpublished", "own", "type", "numplays"]].loc[df_collection["numplays"] != 0].
              reset_index())
    under_cut = len(played.loc[df_collection["yearpublished"] < cut_year])
    played["yearpublished"] = played["yearpublished"].clip(lower=cut_year-1)

    if not toggle_owned:
        played = played.query('own == 1')
    if not toggle_collection:
        played = played.query('type == "boardgame"')
    if len(played) == 0:
        return pd.DataFrame()

    played = played.groupby("yearpublished").count().reset_index()
    played.drop(["index", "own", "type", "numplays"], inplace=True, axis=1)
    played["yearpublished"] = played["yearpublished"].astype("str")
    if under_cut > 0:
        played.loc[0, "yearpublished"] = "-" + str(cut_year)
    played.rename(columns={"name": "Quantity"}, inplace=True)
    played.rename(columns={"yearpublished": "Games (tried already) published that year"}, inplace=True)

    this_year = datetime.date.today().year
    for year in range(cut_year, this_year+1):
        if str(year) not in played["Games (tried already) published that year"].values:
            new_row = {"Games (tried already) published that year": str(year), "Quantity": 0}
            played.loc[len(played)] = new_row

    return played
