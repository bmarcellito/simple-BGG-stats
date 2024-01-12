import streamlit as st
import datetime
from plotly import express as px

from present_stats.add_description import add_description
from present_stats.by_publication_year.calculate_games_by_publication_year import \
    calculate_games_by_publication_year
from present_stats.by_publication_year.calculate_plays_by_publication_year import calculate_age_of_games_played
from main_screen_functions.bgg_data_class import BggData


def present_by_publication_year(my_bgg_data: BggData) -> None:
    def graph_1() -> None:
        st.subheader("Games tried grouped by year of publication")
        this_year = datetime.date.today().year - 1
        cut_year = st.slider('Which year to start from?', min_value=1900, max_value=this_year, value=2000)
        with st.spinner('Please wait, calculating statistics...'):
            played = calculate_games_by_publication_year(my_bgg_data.user_collection, my_bgg_data.game_info_db,
                                                         st.session_state.toggle_owned,
                                                         st.session_state.toggle_expansion, cut_year)
        if len(played) == 0:
            st.write("No data to show :(")
        else:
            st.line_chart(played, x="Games (tried already) published that year", y="Quantity", height=400)

    def graph_2() -> None:
        st.subheader("Age of games played with each year")
        with st.spinner('Please wait, calculating statistics...'):
            df_result = calculate_age_of_games_played(my_bgg_data.game_info_db, my_bgg_data.user_collection,
                                                      my_bgg_data.user_plays,
                                                      st.session_state.toggle_owned, st.session_state.toggle_expansion)
        if len(df_result) == 0:
            st.write("No data to show :(")
            return
        st.toggle(label="Relative / absolute presentation", key="toggle_rel_abs")
        if st.session_state.toggle_rel_abs:
            # absolute presentation
            groupnorm = ""
            title = "Number of games played during that year"
            yaxis = dict()
        else:
            # relative presentation
            groupnorm = "percent"
            title = "Percentage of games played during that year"
            yaxis = dict(type='linear', range=[1, 100], ticksuffix='%')
        y = ["Yet unpublished", "From that year", "1 year old", "2 years old", "3 years old", "4-6 years old",
             "7-10 years old", "11-20 years old", "21-50 years old", "More than 50 years old"]
        fig = px.area(df_result, x="Period", y=y, height=400, groupnorm=groupnorm)
        fig.update_layout(showlegend=True, xaxis_type='category', yaxis_title=title, legend_title="Publication date",
                          yaxis=yaxis)
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    st.caption("Filters for all graphs:")
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")
    graph_1()
    graph_2()
    add_description("plays_by_publication")
    return None
