import re
import pandas as pd


def calculate_bgg_toplist(historic: pd.DataFrame, plays: pd. DataFrame, sel_year: str) -> pd.DataFrame:
    # create list of date we have ranking information
    periods = []
    column_list = historic.columns.values
    for item in column_list:
        if re.match(r'\d{4}-\d{2}-\d{2}', item):
            periods.append(item)
    if len(periods) == 0 or len(plays) == 0:
        return pd.DataFrame()

    to_filter = periods
    periods = []
    from_year = int(sel_year)
    for item in to_filter:
        this_item = int(item[:4])
        if this_item >= from_year:
            periods.append(item)

    # create list of games with their first play dates
    df_plays = plays.groupby(["name", "objectid"])[["date"]].min()

    df_result = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300", "top 400", "top 500",
                                      "top1000", "top2000"])
    df_result_cum = pd.DataFrame(columns=["Date", "top 100", "top 200", "top 300",
                                          "top 400", "top 500", "top1000", "top2000"])

    for i in range(len(periods)):
        ranking = historic[["objectid", periods[i]]]
        df_known = df_plays[df_plays["date"] <= periods[i]]
        df_known = pd.merge(df_known, ranking, how="left", on="objectid")
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
    return df_result_cum
