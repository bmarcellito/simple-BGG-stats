import pandas as pd
import streamlit as st
import datetime

from present_stats.add_description import add_description
from present_stats.games_by_publication_year.calculate_games_by_publication_year import \
    calculate_games_by_publication_year


def present_games_by_publication_year() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")
        this_year = datetime.date.today().year - 1
        cut_year = st.slider('Which year to start from?', 1900, this_year, 2000)

        with st.spinner('Please wait, calculating statistics...'):
            played = calculate_games_by_publication_year(st.session_state.my_collection,
                                                         st.session_state.global_game_infodb,
                                                         st.session_state.toggle_owned,
                                                         st.session_state.toggle_expansion, cut_year)

        if len(played) == 0:
            st.write("No data to show :(")
        else:
            st.line_chart(played, x="Games (tried already) published that year", y="Quantity", height=400)
            with st.expander("Numerical data"):
                played.index = pd.RangeIndex(start=1, stop=len(played) + 1, step=1)
                st.table(played)
            add_description("games_by_publication")
    return None
