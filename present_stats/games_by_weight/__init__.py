import streamlit as st

from present_stats.games_by_weight.calculate_games_by_weight import calculate_games_by_weight
from present_stats.add_description import add_description


def present_games_by_weight() -> None:
    st.session_state.ph_stat = st.empty()
    with (st.session_state.ph_stat.container()):
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")

        df_weight = calculate_games_by_weight(st.session_state.global_game_infodb, st.session_state.my_collection,
                                              st.session_state.my_plays, st.session_state.toggle_owned,
                                              st.session_state.toggle_expansion)
        if len(df_weight) == 0:
            st.write("No data to show :(")
        else:
            st.subheader("Distribution of the known games' weight")
            st.line_chart(df_weight, x="Weight", y="Known games", height=400)
            st.subheader("Distribution of the plays' weight")
            st.line_chart(df_weight, x="Weight", y="Played games", height=400)
            add_description("games_by_weight")
    return None
