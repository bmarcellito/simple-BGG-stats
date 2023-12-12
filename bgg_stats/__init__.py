import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

import re


@st.cache_data(ttl=86400)
def add_description(title: str, method="explanation") -> None:
    df = pd.read_csv("bgg_stats/stat_desc.csv", index_col="topic")
    text_to_show = df.at[title, "description"]
    match method:
        case "explanation":
            with st.expander("See explanation"):
                st.markdown(text_to_show)
        case "description":
            st.write(text_to_show)
    return None


def basics(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_info: pd.DataFrame) -> None:
    df_game_info_fresh = df_game_info.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)

    collection_merged = pd.merge(df_collection, df_game_info_fresh, how="left", on="objectid")
    plays_merged = pd.merge(df_plays, df_game_info_fresh, how="left", on="objectid")
    collection_all = len(collection_merged)
    collection_games = len(collection_merged.query('type == "boardgame"'))
    collection_exp = len(collection_merged.query('type == "boardgameexpansion"'))
    owned_all = df_collection["own"].loc[df_collection["own"] == 1].count()
    owned_games = len(collection_merged.query('(type == "boardgame") and (own == 1)'))
    owned_exp = len(collection_merged.query('(type == "boardgameexpansion") and (own == 1)'))
    plays_all = df_plays["quantity"].sum()
    plays_games = plays_merged.query('type == "boardgame"')
    plays_games = plays_games["quantity"].sum()
    plays_exp = plays_merged.query('type == "boardgameexpansion"')
    plays_exp = plays_exp["quantity"].sum()
    tried_all = df_plays["objectid"].nunique()
    tried_games = plays_merged.query('type == "boardgame"')
    tried_games = tried_games["objectid"].nunique()
    tried_exp = plays_merged.query('type == "boardgameexpansion"')
    tried_exp = tried_exp["objectid"].nunique()
    rated_all = len(collection_merged.query('user_rating > 0'))
    rated_games = len(collection_merged.query('(type == "boardgame") and (user_rating > 0)'))
    rated_exp = len(collection_merged.query('(type == "boardgameexpansion") and (user_rating > 0)'))
    more_all = df_collection["numplays"].loc[df_collection["numplays"] > 1].count()
    more_games = len(collection_merged.query('(type == "boardgame") and (numplays > 1)'))
    more_exp = len(collection_merged.query('(type == "boardgameexpansion") and (numplays > 1)'))
    data = {"Name": ["Size of BGG collection", "Number of items owned", "Number of recorded plays",
                     "Number of unique items tried", "Played more than once",
                     "Number of items rated by the user"],
            "Games": [collection_games, owned_games, plays_games, tried_games, more_games, rated_games],
            "Expansions": [collection_exp, owned_exp, plays_exp, tried_exp, more_exp, rated_exp],
            "All": [collection_all, owned_all, plays_all, tried_all, more_all, rated_all]}
    df_basic = pd.DataFrame(data, index=pd.RangeIndex(start=1, stop=7, step=1))
    st.dataframe(df_basic, use_container_width=True)

    st.write(f'First play recorded on: {df_plays.date.min()}')
    st.write(f'Mean of plays with a specific game: {df_collection["numplays"].mean():.2f}')
    st.write(f'Median of plays with a specific game: {df_collection["numplays"].median()}')

    add_description("basics")
    return None


def favourite_games(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Favourite games")
    st.checkbox('Include boardgame expansions as well', key="h_index_favor")
    df_favourite_games = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_favourite_games = pd.DataFrame(df_favourite_games.loc[df_favourite_games["user_rating"] > 0])
    if "h_index_favor" in st.session_state:
        if not st.session_state.h_index_favor:
            df_favourite_games = df_favourite_games.query('type == "boardgame"')

    df_favourite_games = df_favourite_games.sort_values(by=["user_rating", "numplays", "own"], ascending=False).head(30)
    df_favourite_games = df_favourite_games[['name', 'user_rating', 'yearpublished', 'numplays',  'image', 'objectid']]
    df_favourite_games["objectid"] = df_favourite_games["objectid"].astype("str")
    df_favourite_games.rename(columns={"objectid": "link"}, inplace=True)

    pos = df_favourite_games.columns.get_loc("link")
    for i in range(len(df_favourite_games)):
        df_favourite_games.iloc[i, pos] = f'https://boardgamegeek.com/boardgame/{df_favourite_games.iloc[i, pos]}'

    df_favourite_games.index = pd.RangeIndex(start=1, stop=len(df_favourite_games) + 1, step=1)

    st.dataframe(df_favourite_games, use_container_width=True,
                 column_config={"image": st.column_config.ImageColumn("Image", width="small"),
                                "link": st.column_config.LinkColumn("BGG link", width="small")})


def favourite_designers(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Favourite designers")
    st.selectbox("How to measure?", ("Favourite based on number of games known", "Favourite based on plays",
                                     "Favourite based on user' ratings"), key='sel_designer')

    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df_favourite_designer = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_favourite_designer = df_favourite_designer.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_favourite_designer = df_favourite_designer.query('type == "boardgame"')

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
    if 'sel_designer' not in st.session_state:
        st.session_state.sel_designer = 'Favourite based on number of games known'
    match st.session_state.sel_designer:
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
    st.table(df_favourite_designer)
    add_description("favourite_designers")


def stat_not_played(df_collection: pd.DataFrame) -> None:
    # st.subheader("Owned games not played yet")
    games_owned = df_collection.loc[df_collection["own"] == 1]
    not_played = pd.DataFrame(games_owned["name"].loc[games_owned["numplays"] == 0].sort_values())
    if not_played.empty:
        st.write("Congratulation, you have already played with all games you currently own!")
    else:
        not_played.index = pd.RangeIndex(start=1, stop=len(not_played) + 1, step=1)
        st.table(not_played)


def games_by_publication(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Games tried grouped by year of publication")
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items of the collection", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")
    cut_year = st.slider('Which year to start from?', 1950, 2020, 2000)

    played = df_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    played = (played[["name", "yearpublished", "own", "type", "numplays"]].loc[df_collection["numplays"] != 0].
              reset_index())
    under_cut = len(played.loc[df_collection["yearpublished"] <= cut_year])
    played["yearpublished"] = played["yearpublished"].clip(lower=cut_year)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            played = played.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            played = played.query('type == "boardgame"')

    played = played.groupby("yearpublished").count().reset_index()
    played.drop(["index", "own", "type", "numplays"], inplace=True, axis=1)
    if under_cut > 0:
        played["yearpublished"] = played["yearpublished"].astype("str")
        played.loc[0, "yearpublished"] = "-" + str(cut_year)
    played.rename(columns={"name": "Quantity"}, inplace=True)
    played.rename(columns={"yearpublished": "Games published that year known"}, inplace=True)

    st.line_chart(played, x="Games published that year known", y="Quantity", height=400)
    with st.expander("Numerical data"):
        played.index = pd.RangeIndex(start=1, stop=len(played) + 1, step=1)
        st.table(played)

    add_description("games_by_publication")


def plays_by_publication(df_plays: pd.DataFrame, df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    # st.subheader("Games tried grouped by year of publication")
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items of the collection", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")
    cut_year = st.slider('Which year to start from?', 1950, 2020, 2000)

    played = df_plays.merge(df_collection, how="left", on="objectid", suffixes=("", "_y"))
    played.drop(["yearpublished"], inplace=True, axis=1)
    played = played.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))

    played = played[["name", "date", "quantity", "year_published", "own", "type"]]
    played.rename(columns={"year_published": "yearpublished"}, inplace=True)

    under_cut = len(played.loc[played["yearpublished"] <= cut_year])
    played["yearpublished"] = played["yearpublished"].clip(lower=cut_year)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            played = played.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            played = played.query('type == "boardgame"')

    played.drop(["own", "type"], inplace=True, axis=1)
    played = pd.DataFrame(played.groupby(["yearpublished", "date"], sort=False).sum())
    played = played.reset_index()
    played.rename(columns={"yearpublished": "Year published"}, inplace=True)

    # if under_cut > 0:
    #     played["Year published"] = played["Year published"].astype("str")
    #     played.loc[0, "Year published"] = "-" + str(cut_year)

    played = played.query('quantity > 0')

    fig = px.scatter(played, y="Year published", x="date", size="quantity",
                     hover_name="name", height=600)
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    add_description("plays_by_publication")


def h_index(df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    def count_h(df_raw: pd.DataFrame) -> (pd.DataFrame, int):
        if df_raw.empty:
            return df_raw, 0
        df_count = df_raw.groupby("Name", sort=False).sum().reset_index()
        df_count = df_count.sort_values(by=["Number of plays", "Name"], ascending=[False, True]).reset_index()
        i = 0
        while 0 == 0:
            try:
                if df_count.iloc[i]["Number of plays"] < i + 1:
                    break
            except IndexError:
                break
            i += 1

        df_player_num_votes = pd.DataFrame(df_count[["Name", "Number of plays"]].loc[df_count["Number of plays"] >= i])
        if len(df_player_num_votes) > i:
            extra_text = "Also in the H-index range are: "
            for index in range(i, len(df_player_num_votes)):
                extra_text = (f'{extra_text}{df_player_num_votes.at[index, "Name"]} '
                              f'({df_player_num_votes.at[index, "Number of plays"]} plays), ')
            extra_text = extra_text[:-2]
            df_player_num_votes.at[i, "Name"] = extra_text
            df_player_num_votes["Number of plays"] = df_player_num_votes["Number of plays"].astype(str)
            df_player_num_votes.at[i, "Number of plays"] = f'At least {i}'
            cut = i+1
        else:
            cut = i
        df_player_num_votes.index = pd.RangeIndex(start=1, stop=len(df_player_num_votes) + 1, step=1)
        return df_player_num_votes.head(cut), i

    # st.subheader("H-index")
    st.selectbox("Show data from period...", ('All times', 'Last year (starting from today)',
                                              'For each calendar year'), key='sel_hindex')

    st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df_game_infodb_fresh = df_game_infodb.drop_duplicates(subset=["objectid"], keep="last", ignore_index=True)
    df = pd.merge(df_plays, df_game_infodb_fresh, how="left", on="objectid", suffixes=("", "_y"))
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df = df.query('type == "boardgame"')
    df = df[["name", "quantity", "date"]]
    df.rename(columns={"name": "Name", "quantity": "Number of plays", "date": "Date"}, inplace=True)
    df = df.reset_index()

    if 'sel_hindex' not in st.session_state:
        st.session_state.sel_hindex = 'All times'
    match st.session_state.sel_hindex:
        case 'All times':
            df_result, i = count_h(df)
            st.write(f'H-index is {i}. Games within the H-index:')
            st.table(df_result)
        case 'Last year (starting from today)':
            no_row = len(df)
            one_years_ago = datetime.today() - timedelta(days=365)
            for index in range(no_row):
                play_date = datetime.strptime(df.at[index, "Date"], "%Y-%m-%d")
                if play_date > one_years_ago:
                    df.at[index, "Date"] = 1
                else:
                    df.at[index, "Date"] = 0
            df = df.query(f'Date == 1')
            df_result, i = count_h(df)
            st.write(f'H-index is {i}. Games within the H-index:')
            st.table(df_result)
        case 'For each calendar year':
            df["Date"] = df["Date"].str[0:4].astype(int)
            df = df.sort_values("Date").reset_index(drop=True)
            plays_years = df["Date"].unique().tolist()
            no_row = len(plays_years)
            for index in range(no_row):
                df_yearly = df.query(f'Date == {plays_years[index]}')
                df_result, i = count_h(df_yearly)
                with st.expander(f'For year {plays_years[index]} the H-index is {i}.'):
                    st.table(df_result)

    add_description("h-index")
    return None


def yearly_plays(df_play_stat: pd.DataFrame) -> None:
    # st.subheader("Play statistics by year")
    # number of new games tried in every year
    df_new_games = df_play_stat.groupby(["name", "objectid"])[["date"]].min()
    df_new_games["year"] = df_new_games["date"].str[0:4].astype(int)
    df_new_games = df_new_games.groupby("year").count()
    df_new_games.rename(columns={"date": "New games tried"}, inplace=True)

    # number of unique games known already at that time
    df_new_games["known_games"] = df_new_games["New games tried"].cumsum()
    df_new_games.rename(columns={"known_games": "Known games"}, inplace=True)

    # number of unique games played in every year
    df_played = df_play_stat
    df_played["year"] = df_played["date"].str[0:4].astype(int)
    df_played = pd.Series(df_played.groupby("year")["objectid"].nunique())
    df_played.rename("Unique games played", inplace=True)

    # number of all plays in every year
    df_all_plays = df_play_stat
    df_all_plays["year"] = df_all_plays["date"].str[0:4].astype(int)
    df_all_plays = df_all_plays.groupby("year")["quantity"].sum()
    df_all_plays.rename("Number of plays", inplace=True)

    df_result = pd.merge(df_new_games, df_played, how="left", on="year")
    df_result = (pd.merge(df_result, df_all_plays, how="left", on="year").sort_values("year", ascending=False).
                 reset_index())

    st.dataframe(df_result, hide_index=True, use_container_width=True)
    add_description("yearly_plays")
    return None


def historic_ranking(historic: pd.DataFrame, plays: pd. DataFrame) -> None:
    # st.subheader("Games known from BGG top list")
    # method = st.selectbox("How to show data?", ('Basic', 'Cumulative'), key='TOP100')
    # TODO add years from DB
    st.selectbox("Show data from year...", ('2017', '2018', '2019', '2020', '2021'), key='sel_year')
    # st.selectbox("Data sampling", ('Yearly', 'Quarterly', 'Monthly'), key='sel_sampling')

    # create list of date we have ranking information
    periods = []
    column_list = historic.columns.values
    for item in column_list:
        if re.match(r'\d{4}-\d{2}-\d{2}', item):
            periods.append(item)

    to_filter = periods
    periods = []
    if 'sel_year' not in st.session_state:
        st.session_state.sel_year = '2017'
    from_year = int(st.session_state.sel_year)
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

    st.line_chart(df_result_cum, x="Date", height=600)
    with st.expander("Numerical presentation"):
        st.dataframe(df_result_cum, hide_index=True, use_container_width=True)

    add_description("historic_ranking")
    return None


def by_weight(df_game_info: pd.DataFrame, df_collection: pd.DataFrame, df_plays: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items played", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    most_played = pd.DataFrame(df_plays.groupby("objectid")["quantity"].sum())
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played = most_played.merge(df_game_info, how="left", on="objectid", suffixes=("", "_y"))
    most_played = most_played.merge(df_collection, how="left", on="objectid", suffixes=("", "_y"))
    most_played["year_published"] = most_played["year_published"].clip(1990)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            most_played = most_played.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            most_played = most_played.query('type == "boardgame"')

    most_played = most_played[["objectid", "type", "name", "year_published", "weight", "quantity", "rating_average"]]
    most_played = most_played.sort_values("quantity", ascending=False)
    most_played.rename(columns={"rating_average": "Average rating on BGG", "weight": "Weight",
                                "quantity": "Number of plays"}, inplace=True)
    fig = px.scatter(most_played, x="Average rating on BGG", y="Weight", size="Number of plays",
                     hover_name="name", height=600)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    add_description("by_weight")
    return None


def by_rating(df_collection: pd.DataFrame, df_plays: pd.DataFrame, df_game_infodb: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items played", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")

    df_rating = pd.merge(df_collection, df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_rating = pd.DataFrame(df_rating.loc[df_rating["user_rating"] > 0])

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_rating = df_rating.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_rating = df_rating.query('type == "boardgame"')

    most_played = pd.DataFrame(df_plays.groupby("objectid").sum())
    df_rating = df_rating.merge(most_played, how="left", left_on="objectid", right_on="index", suffixes=("", "_z"))
    df_rating = df_rating[["name", "numplays", "user_rating", "rating_average"]]
    df_rating.rename(columns={"user_rating": "User's rating", "rating_average": "Average rating on BGG",
                              "numplays": "Number of plays"}, inplace=True)
    df_rating = df_rating.sort_values(by="Number of plays", ascending=False)
    df_rating["color_data"] = "Data"

    max_size = max(df_rating["Number of plays"].max() // 100, 1)
    if max_size == 1:
        circle_size = max_size*10
    else:
        circle_size = max_size*4
    step = max_size*5
    for i in range(step*10):
        new_row = pd.DataFrame({"name": "", "Number of plays": max_size, "User's rating": i/step,
                                "Average rating on BGG": i/step, "color_data": "Equal values line"},
                               index=[len(df_rating)])
        df_rating = pd.concat([df_rating, new_row])

    fig = px.scatter(df_rating, x="Average rating on BGG", y="User's rating", size="Number of plays",
                     hover_name="name", color="color_data", color_discrete_sequence=["#000000", "#FB0D0D"],
                     size_max=circle_size)
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    add_description("by_rating")
    return None


def collection(df_collection: pd.DataFrame, df_game_infodb: pd.DataFrame, df_playnum_infodb: pd.DataFrame) -> None:
    def calculate_ideal_player_number():
        row_no = len(df_updated_collection)
        for index in range(row_no):
            feedback = [0, 0, 0, 0, 0, 0, 0, 0]
            object_id = int(df_updated_collection.at[index, "objectid"])
            try:
                min_player = int(df_updated_collection.at[index, "min_player"])
            except ValueError:
                min_player = 0
            try:
                max_player = min(int(df_updated_collection.at[index, "max_player"]), 8)
            except ValueError:
                max_player = 0
            player_info = df_playnum_infodb.query(f'objectid == {object_id}').reset_index()
            inner_row_no = len(player_info)
            if inner_row_no == 0:
                df_updated_collection.at[index, "objectid"] = 0
                df_updated_collection.at[index, "own"] = feedback
                continue
            for j in range(inner_row_no):
                current_playernum = int(player_info.at[j, "numplayers"])
                if min_player <= current_playernum <= max_player:
                    best = int(player_info.at[j, "best"])
                    rec = int(player_info.at[j, "recommended"] * 1)
                    not_rec = int(player_info.at[j, "not recommended"])
                    feedback[current_playernum - 1] = best * 3 + rec + not_rec * 0
                else:
                    continue
            votes = sum(feedback)
            if votes > 0:
                for k in range(8):
                    feedback[k] = (feedback[k] * 100) // votes
            df_updated_collection.at[index, "objectid"] = feedback.index(max(feedback)) + 1
            df_updated_collection.at[index, "own"] = feedback

    # st.subheader("Ideal number of players for each game you own")
    col1, col2 = st.columns(2)
    with col1:
        if "h_toggle_owned" not in st.session_state:
            st.session_state.h_toggle_owned = False
        if st.session_state.h_toggle_owned:
            st.toggle("Toggle it to show only the items owned", key="h_toggle_owned", value=True)
        else:
            st.toggle("Toggle it to show all items of the collection", key="h_toggle_owned")
    with col2:
        st.toggle('Include boardgame expansions as well', key="h_toggle_collection")
    player_range = st.slider('Narrow on ideal player number', 1, 8, (1, 8), key='stat_playernum')

    df_ordered_collection = df_collection.sort_values("name").reset_index(drop=True)
    df_updated_collection = df_ordered_collection.merge(df_game_infodb, how="left", on="objectid", suffixes=("", "_y"))
    df_updated_collection.drop_duplicates(subset=["objectid"], keep="last", inplace=True, ignore_index=True)

    if "h_toggle_owned" in st.session_state:
        if not st.session_state.h_toggle_owned:
            df_updated_collection = df_updated_collection.query('own == 1')
    if "h_toggle_collection" in st.session_state:
        if not st.session_state.h_toggle_collection:
            df_updated_collection = df_updated_collection.query('type == "boardgame"')
    df_updated_collection.reset_index(drop=True, inplace=True)
    df_updated_collection = df_updated_collection[["name", "numplays", "user_rating", "weight",
                                                   "min_player", "max_player", "objectid",
                                                   "own", "image", "thumbnail"]]
    df_updated_collection["own"] = df_updated_collection["own"].astype(object)

    # create link for the item
    df_updated_collection = pd.DataFrame(df_updated_collection.rename(columns={"thumbnail": "Link"}))
    pos_link = df_updated_collection.columns.get_loc("Link")
    pos_objectid = df_updated_collection.columns.get_loc("objectid")
    for i in range(len(df_updated_collection)):
        df_updated_collection.iloc[i, pos_link] = \
            f'https://boardgamegeek.com/boardgame/{df_updated_collection.iloc[i, pos_objectid]}'

    calculate_ideal_player_number()

    if "stat_playernum" not in st.session_state:
        player_range = (1, 8)
    df_updated_collection["objectid"] = df_updated_collection["objectid"].astype(int)
    df_updated_collection = df_updated_collection.query(f'objectid >= {player_range[0]}')
    df_updated_collection = df_updated_collection.query(f'objectid <= {player_range[1]}')

    df_updated_collection.columns = ["Name", "No plays", "User\'s rating", "Weight", "Min player", "Max player",
                                     "Ideal player no", "BGG votes on player numbers", "Image", "Link"]
    st.dataframe(df_updated_collection, column_config={
        "BGG votes on player numbers": st.column_config.BarChartColumn(
            help="BGG users' feedback on specific player numbers (1-8 players shown)", y_min=0, y_max=100),
        "Image": st.column_config.ImageColumn("Image", width="small"),
        "Weight": st.column_config.NumberColumn(format="%.2f"),
        "Link": st.column_config.LinkColumn("BGG link", width="small")
    }, hide_index=True, use_container_width=True)

    add_description("collection")
    return None
