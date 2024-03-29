import streamlit as st
from plotly import express as px

from present_stats.games_by_weight.calculate_games_by_weight import calculate_games_by_weight
from present_stats.games_by_weight.calculate_plays_weight import calculate_plays_weight
from present_stats.add_description import add_description
from main_screen_functions.bgg_data_class import BggData


def present_games_by_weight(my_bgg_data: BggData) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

    with st.spinner('Please wait, calculating statistics...'):
        df_weight = calculate_games_by_weight(my_bgg_data.game_info_db, my_bgg_data.user_collection,
                                              my_bgg_data.user_plays,
                                              st.session_state.toggle_owned, st.session_state.toggle_expansion)

    if len(df_weight) == 0:
        st.write("No data to show :(")
    else:
        st.subheader("Distribution of the known games' weight")
        fig = px.histogram(df_weight, x="Weight", y="Known games", height=400, range_x=[0.5, 5.5], nbins=10,
                           text_auto=True)
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        st.subheader("Distribution of the plays' weight")
        fig = px.histogram(df_weight, x="Weight", y="Played games", height=400, range_x=[0.5, 5.5], nbins=10,
                           text_auto=True)
        fig.update_layout(bargap=0.1)
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        with st.spinner('Please wait, calculating statistics...'):
            df_plays = calculate_plays_weight(my_bgg_data.user_plays, my_bgg_data.game_info_db,
                                              st.session_state.toggle_expansion)

        if len(df_plays) == 0:
            st.write("No data to show :(")
        else:
            st.line_chart(df_plays, x="Date", y=["Average weight of monthly plays", "Rolling window average"],
                          height=400)
        add_description("games_by_weight")
    return None
