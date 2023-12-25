import streamlit as st
from datetime import datetime


from present_stats.bgg_toplist.calculate_bgg_toplist import calculate_bgg_toplist
from present_stats.add_description import add_description


def present_bgg_toplist() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        this_year = str(datetime.date(datetime.today()))
        this_year = int(this_year[0:4])
        list_of_year = []
        for i in range(2017, this_year+1):
            list_of_year.append(i)
        st.selectbox("Show data from year...", list_of_year, key='sel_year')

        with st.spinner('Please wait, calculating statistics...'):
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
