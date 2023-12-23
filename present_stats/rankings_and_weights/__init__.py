import streamlit as st
from plotly import express as px
import statsmodels

from present_stats.rankings_and_weights.calculate_rankings_and_weights import calculate_rankings_and_weights
from present_stats.add_description import add_description


def present_rankings_and_weights() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_collection")
        most_played, min_weight, max_weight, min_rating, max_rating = calculate_rankings_and_weights(
            st.session_state.global_game_infodb, st.session_state.my_collection, st.session_state.my_plays,
            st.session_state.toggle_owned, st.session_state.toggle_collection)
        if len(most_played) == 0:
            st.write("No data to show :(")
        else:
            fig = px.scatter(most_played, x="Average rating on BGG", y="Weight", size="Number of plays",
                             hover_name="name", height=600, trendline="ols",
                             range_x=[min_rating, max_rating], range_y=[min_weight, max_weight])
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
            add_description("by_weight")
    return None
