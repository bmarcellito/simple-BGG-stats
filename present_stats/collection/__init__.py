import streamlit as st
from present_stats.add_description import add_description
from present_stats.collection.calculate_collection import calculate_collection


def present_collection():
    st.session_state.ph_stat = st.empty()
    with st.session_state.ph_stat.container():
        col1, col2 = st.columns(2)
        with col1:
            st.toggle(label="Just owned games / all known games", key="toggle_owned")
        with col2:
            st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")
        player_range = st.slider('Narrow on ideal player number', 1, 8, (1, 8), key='stat_playernum')

        with st.spinner('Please wait, calculating statistics...'):
            stat = calculate_collection(st.session_state.my_collection, st.session_state.global_game_infodb,
                                        st.session_state.global_play_numdb, st.session_state.toggle_owned,
                                        st.session_state.toggle_expansion, player_range)

        if len(stat) == 0:
            st.write("No data to show :(")
        else:
            st.dataframe(stat, column_config={
                "BGG votes on player numbers": st.column_config.BarChartColumn(
                    help="BGG users' feedback on specific player numbers (1-8 players shown)", y_min=0, y_max=100),
                "Image": st.column_config.ImageColumn("Image", width="small"),
                "Weight": st.column_config.NumberColumn(format="%.2f"),
                "Link": st.column_config.LinkColumn("BGG link", width="small")
            }, hide_index=True, use_container_width=True)
            add_description("collection")
    return None
