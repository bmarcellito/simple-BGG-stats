import streamlit as st

from present_stats.add_description import add_description
from present_stats.plays_by_years.calculate_plays_by_years import calculate_plays_by_years
from main_screen_functions.bgg_data_class import BggData


def present_plays_by_years(my_bgg_data: BggData) -> None:
    with st.spinner('Please wait, calculating statistics...'):
        df_result = calculate_plays_by_years(my_bgg_data.user_plays)

    if len(df_result) == 0:
        st.write("No data to show :(")
    else:
        st.dataframe(df_result, hide_index=True, use_container_width=True)
        add_description("yearly_plays")
    return None
