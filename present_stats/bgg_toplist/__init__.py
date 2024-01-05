import streamlit as st
from datetime import datetime

from present_stats.bgg_toplist.calculate_bgg_toplist import calculate_bgg_toplist
from present_stats.add_description import add_description
from bgg_import.get_functions import get_historic_rankings
from main_screen_functions.bgg_data_class import BggData


def present_bgg_toplist(my_bgg_data: BggData) -> None:
    this_year = datetime.today().year
    cut_year = st.slider('Which year to start from?', min_value=2017, max_value=this_year)

    with st.spinner('Please wait, calculating statistics...'):
        df_historic_rankings = get_historic_rankings()
        df_result_cum = calculate_bgg_toplist(df_historic_rankings, my_bgg_data.user_plays, cut_year)

    if len(df_result_cum) == 0:
        st.write("No data to show :(")
    else:
        st.line_chart(df_result_cum, x="Date", height=600)
        with st.expander("Numerical presentation"):
            st.dataframe(df_result_cum, hide_index=True, use_container_width=True)
        add_description("bgg_toplist")
    del df_historic_rankings
    return None
