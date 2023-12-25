import pandas as pd


def calculate_age_of_games_played(df_game_infodb: pd.DataFrame, df_collection: pd.DataFrame,
                                  df_plays: pd.DataFrame, toggle_owned: bool,
                                  toggle_expansion: bool) -> pd.DataFrame:
    if len(df_plays) == 0:
        return pd.DataFrame()
    processed_play = pd.merge(df_plays, df_game_infodb[["objectid", "name", "type", "year_published"]], how="left",
                              on="objectid", suffixes=("", "_y"))
    processed_play = processed_play.merge(df_collection[["objectid", "own"]], how="left", on="objectid",
                                          suffixes=("", "_y"))
    processed_play.reset_index(inplace=True)
    for i in range(len(processed_play)):
        processed_play.at[i, "date"] = processed_play.at[i, "date"][0:4]

    possible_dates = processed_play["date"].tolist()
    # remove duplicates
    possible_dates = list(set(possible_dates))

    # create template table
    df_plays_by_pub = pd.DataFrame(
        columns=["Period", "Yet_unpublished", "From_that_year", "1_year_old", "2_years_old", "3_years_old",
                 "4-6_years_old", "7-10_years_old", "11-20_years_old", "21-50_years_old", "More_than_50_years_old"])
    possible_dates.sort()
    for i in range(len(possible_dates)):
        row_no = len(df_plays_by_pub)
        df_plays_by_pub.loc[row_no] = [possible_dates[i], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    if not toggle_owned:
        processed_play = processed_play.query('own == 1')
    if not toggle_expansion:
        processed_play = processed_play.query('type == "boardgame"')
    if len(processed_play) == 0:
        return pd.DataFrame()

    processed_play.sort_values(by="date")
    date_index = processed_play.columns.get_loc('date')
    quantity_index = processed_play.columns.get_loc('quantity')
    published_index = processed_play.columns.get_loc('year_published')
    for i in range(len(processed_play)):
        period = processed_play.iat[i, date_index]
        difference = int(processed_play.iat[i, date_index][0:4]) - int(processed_play.iat[i, published_index])
        row_index = df_plays_by_pub[df_plays_by_pub["Period"] == period].index.values[0]
        match difference:
            case x if x < 0:
                df_plays_by_pub.at[row_index, "Yet_unpublished"] += processed_play.iat[i, quantity_index]
            case x if x == 0:
                df_plays_by_pub.at[row_index, "From_that_year"] += processed_play.iat[i, quantity_index]
            case x if x == 1:
                df_plays_by_pub.at[row_index, "1_year_old"] += processed_play.iat[i, quantity_index]
            case x if x == 2:
                df_plays_by_pub.at[row_index, "2_years_old"] += processed_play.iat[i, quantity_index]
            case x if x == 3:
                df_plays_by_pub.at[row_index, "3_years_old"] += processed_play.iat[i, quantity_index]
            case x if (x > 3) and (x < 7):
                df_plays_by_pub.at[row_index, "4-6_years_old"] += processed_play.iat[i, quantity_index]
            case x if (x > 6) and (x < 11):
                df_plays_by_pub.at[row_index, "7-10_years_old"] += processed_play.iat[i, quantity_index]
            case x if (x > 10) and (x < 21):
                df_plays_by_pub.at[row_index, "11-20_years_old"] += processed_play.iat[i, quantity_index]
            case x if (x > 20) and (x < 51):
                df_plays_by_pub.at[row_index, "21-50_years_old"] += processed_play.iat[i, quantity_index]
            case x if x > 50:
                df_plays_by_pub.at[row_index, "More_than_50_years_old"] += processed_play.iat[i, quantity_index]
    df_plays_by_pub.columns = ["Period", "Yet unpublished", "From that year", "1 year old", "2 years old",
                               "3 years old", "4-6 years old", "7-10 years old", "11-20 years old", "21-50 years old",
                               "More than 50 years old"]
    return df_plays_by_pub
