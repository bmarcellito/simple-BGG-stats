import streamlit as st

from present_stats.add_description import add_description
from present_stats.h_index.calculate_h_index import calculate_h_index, calculate_h_index_graph
from main_screen_functions.presentation_hack import clear_ph_element
from main_screen_functions.bgg_data_class import BggData


def different_h_stat_selected(h_index_container) -> None:
    clear_ph_element([h_index_container])


def present_h_index(my_bgg_data: BggData) -> None:
    h_index_selectbox = st.empty()
    h_index_toggle = st.empty()
    h_index_container = st.empty()

    h_index_selectbox.selectbox("Show data from period...",
                                ('All times', 'For each calendar year'),
                                key='sel_h_index', on_change=different_h_stat_selected, args=[h_index_container])
    st.session_state.toggle_expansion = h_index_toggle.toggle('Include boardgame expansions as well')

    with st.spinner('Please wait, calculating statistics...'):
        result_graph = calculate_h_index_graph(my_bgg_data.user_plays, my_bgg_data.game_info_db,
                                               st.session_state.toggle_expansion)
        result = calculate_h_index(my_bgg_data.user_plays, my_bgg_data.game_info_db,
                                   st.session_state.toggle_expansion, st.session_state.sel_h_index)

    if len(result) == 0:
        st.write("No data to show :(")
        return None

    with h_index_container.container():
        st.line_chart(result_graph, x="Period", height=600)
        match st.session_state.sel_h_index:
            case 'All times' | 'Last year (starting from today)':
                with st.expander(f'All time H-index is {result[0][0]}. Games within the H-index:'):
                    st.table(result[0][1])
            case 'For each calendar year':
                for index in range(len(result)):
                    with st.expander(f'For year {result[index][2]} the H-index is {result[index][0]}.'):
                        st.table(result[index][1])
    add_description("h-index")
    return None
