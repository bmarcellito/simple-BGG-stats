import streamlit as st

from present_stats.bgg_toplist.calculate_bgg_toplist import calculate_bgg_toplist
from present_stats.add_description import add_description


def present_bgg_toplist() -> None:
    # TODO add years from DB
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        st.selectbox("Show data from year...", ('2017', '2018', '2019', '2020', '2021'), key='sel_year')

        df_result_cum = calculate_bgg_toplist(st.session_state.global_historic_ranking, st.session_state.my_plays,
                                              st.session_state.sel_year)

        if len(df_result_cum) == 0:
            st.write("No data to show :(")
        else:
            st.line_chart(df_result_cum, x="Date", height=600)
            with st.expander("Numerical presentation"):
                st.dataframe(df_result_cum, hide_index=True, use_container_width=True)
            add_description("bgg_toplist")
    return None
