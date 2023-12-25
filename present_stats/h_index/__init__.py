import streamlit as st

from present_stats.add_description import add_description
from present_stats.h_index.calculate_h_index import calculate_h_index
from presentation_hack import new_stat_selected


def present_h_index() -> None:
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        st.selectbox("Show data from period...",
                     ('All times', 'Last year (starting from today)', 'For each calendar year'),
                     key='sel_h_index', on_change=new_stat_selected)
        st.session_state.toggle_expansion = st.toggle('Include boardgame expansions as well')

        with st.spinner('Please wait, calculating statistics...'):
            result = calculate_h_index(st.session_state.my_plays, st.session_state.global_game_infodb,
                                       st.session_state.toggle_expansion, st.session_state.sel_h_index)

        if len(result) == 0:
            st.write("No data to show :(")
            return None

        match st.session_state.sel_h_index:
            case 'All times' | 'Last year (starting from today)':
                st.write(f'H-index is {result[0][0]}. Games within the H-index:')
                st.table(result[0][1])
            case 'For each calendar year':
                for index in range(len(result)):
                    with st.expander(f'For year {result[index][2]} the H-index is {result[index][0]}.'):
                        st.table(result[index][1])
        add_description("h-index")
    return None
