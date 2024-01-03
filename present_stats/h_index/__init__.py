import streamlit as st

from present_stats.add_description import add_description
from present_stats.h_index.calculate_h_index import calculate_h_index
from main_screen_functions.presentation_hack import clear_ph_element
from bgg_import.get_functions import get_game_infodb


def different_h_stat_selected(h_index_container) -> None:
    clear_ph_element(h_index_container)


def present_h_index() -> None:
    h_index_selectbox = st.empty()
    h_index_toggle = st.empty()
    h_index_container = st.empty()

    h_index_selectbox.selectbox("Show data from period...",
                                ('All times', 'Last year (starting from today)', 'For each calendar year'),
                                key='sel_h_index', on_change=different_h_stat_selected, args=[h_index_container])
    st.session_state.toggle_expansion = h_index_toggle.toggle('Include boardgame expansions as well')

    with st.spinner('Please wait, calculating statistics...'):
        df_game_infodb = get_game_infodb()
        result = calculate_h_index(st.session_state.my_plays, df_game_infodb,
                                   st.session_state.toggle_expansion, st.session_state.sel_h_index)

    if len(result) == 0:
        st.write("No data to show :(")
        return None

    with h_index_container.container():
        match st.session_state.sel_h_index:
            case 'All times' | 'Last year (starting from today)':
                st.write(f'H-index is {result[0][0]}. Games within the H-index:')
                st.table(result[0][1])
            case 'For each calendar year':
                for index in range(len(result)):
                    with st.expander(f'For year {result[index][2]} the H-index is {result[index][0]}.'):
                        st.table(result[index][1])
    add_description("h-index")
    del df_game_infodb
    return None
