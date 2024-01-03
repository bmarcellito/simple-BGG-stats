import streamlit as st
from plotly import express as px

from present_stats.add_description import add_description
from present_stats.age_of_games_played.calculate_plays_by_publication_year import \
    calculate_age_of_games_played
from bgg_import.get_functions import get_game_infodb


def present_age_of_games_played() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

    with st.spinner('Please wait, calculating statistics...'):
        df_game_infodb = get_game_infodb()
        df_result = calculate_age_of_games_played(df_game_infodb,
                                                  st.session_state.my_collection,
                                                  st.session_state.my_plays,
                                                  st.session_state.toggle_owned,
                                                  st.session_state.toggle_expansion)
    if len(df_result) == 0:
        st.write("No data to show :(")
    else:
        st.subheader("How old are the board games user plays with?")
        st.toggle(label="Relative / absolute presentation", key="toggle_rel_abs")
        if st.session_state.toggle_rel_abs:
            # absolute presentation
            fig = px.area(df_result,
                          x="Period",
                          y=["Yet unpublished", "From that year", "1 year old", "2 years old", "3 years old",
                             "4-6 years old", "7-10 years old", "11-20 years old", "21-50 years old",
                             "More than 50 years old"],
                          height=400)
            fig.update_layout(
                showlegend=True,
                xaxis_type='category',
                yaxis_title="Number of games played during that year",
                legend_title="Publication date")
        else:
            # relative presentation
            fig = px.area(df_result,
                          x="Period",
                          y=["Yet unpublished", "From that year", "1 year old", "2 years old", "3 years old",
                             "4-6 years old", "7-10 years old", "11-20 years old", "21-50 years old",
                             "More than 50 years old"],
                          height=400,
                          groupnorm='percent')
            fig.update_layout(
                showlegend=True,
                xaxis_type='category',
                yaxis_title="Percentage of games played during that year",
                legend_title="Publication date",
                yaxis=dict(
                    type='linear',
                    range=[1, 100],
                    ticksuffix='%'))
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        add_description("plays_by_publication_year")
        del df_game_infodb
    return None
