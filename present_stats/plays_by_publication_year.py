import pandas as pd
import streamlit as st
from plotly import express as px

from bgg_stats import add_description


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
