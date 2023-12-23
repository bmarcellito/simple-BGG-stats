import pandas as pd
import streamlit as st


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
