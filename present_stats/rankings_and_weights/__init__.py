import streamlit as st
from plotly import express as px
import statsmodels

from present_stats.rankings_and_weights.calculate_rankings_and_weights import calculate_rankings_and_weights
from present_stats.add_description import add_description
from bgg_import.get_functions import get_game_infodb


def present_rankings_and_weights() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

    with st.spinner('Please wait, calculating statistics...'):
        df_game_infodb = get_game_infodb()
        most_played, min_weight, max_weight, min_rating, max_rating = calculate_rankings_and_weights(
            df_game_infodb, st.session_state.my_collection, st.session_state.my_plays,
            st.session_state.toggle_owned, st.session_state.toggle_expansion)
    if len(most_played) == 0:
        st.write("No data to show :(")
    else:
        fig = px.scatter(most_played, x="Average rating on BGG", y="Weight", size="Number of plays",
                         hover_name="name", height=600, trendline="ols", size_max=30,
                         range_x=[min_rating, max_rating], range_y=[min_weight, max_weight])
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        add_description("by_weight")
    del df_game_infodb
    return None
