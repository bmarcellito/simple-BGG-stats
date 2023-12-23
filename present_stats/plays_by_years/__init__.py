import streamlit as st

from present_stats.add_description import add_description
from present_stats.plays_by_years.calculate_plays_by_years import calculate_plays_by_years


def present_plays_by_years() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        df_result = calculate_plays_by_years(st.session_state.my_plays)
        if len(df_result) == 0:
            st.write("No data to show :(")
        else:
            st.dataframe(df_result, hide_index=True, use_container_width=True)
            add_description("yearly_plays")
    return None
