import streamlit as st
from plotly import express as px
import statsmodels

from present_stats.user_and_bgg_ratings.calculate_user_and_bgg_ratings import calculate_user_and_bgg_ratings
from present_stats.add_description import add_description


def present_user_and_bgg_ratings() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

        with st.spinner('Please wait, calculating statistics...'):
            df_rating, min_rating, max_rating, min_bgg_rating, max_bgg_rating = calculate_user_and_bgg_ratings(
                st.session_state.my_collection, st.session_state.my_plays, st.session_state.global_game_infodb,
                st.session_state.toggle_owned, st.session_state.toggle_expansion)

        if len(df_rating) == 0:
            st.write("No data to show :(")
        else:
            fig = px.scatter(df_rating, x="Average rating on BGG", y="User's rating", size="Number of plays",
                             hover_name="name", color="color_data", color_discrete_sequence=["#000000", "#FB0D0D"],
                             size_max=30, range_x=[min_bgg_rating, max_bgg_rating],
                             range_y=[min_rating, max_rating], trendline="ols")
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        add_description("by_rating")
    return None
