import pandas as pd


def calculate_favourite_designers(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame, toggle_owned: bool,
                                  toggle_expansion: bool, stat_type: str) -> pd.DataFrame:

    if len(df_collection) == 0:
        return pd.DataFrame()
    df_favourite_designer = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    if not toggle_owned:
        df_favourite_designer = df_favourite_designer.query('own == 1')
    if not toggle_expansion:
        df_favourite_designer = df_favourite_designer.query('type == "boardgame"')
    if len(df_favourite_designer) == 0:
        return pd.DataFrame()

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
    match stat_type:
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
    return df_favourite_designer
