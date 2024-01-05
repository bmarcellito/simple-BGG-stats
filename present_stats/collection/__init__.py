import streamlit as st

from main_screen_functions.bgg_data_class import BggData
from present_stats.add_description import add_description
from present_stats.collection.calculate_collection import calculate_collection


def present_collection(my_bgg_data: BggData):
    col1, col2 = st.columns(2)
    with col1:
        st.toggle(label="Just owned games / all known games", key="toggle_owned")
    with col2:
        st.toggle(label='Include boardgame expansions as well', key="toggle_expansion")
    player_range = st.slider('Narrow on ideal player number', 1, 8, (1, 8), key='stat_playernum')

    with st.spinner('Please wait, calculating statistics...'):
        stat = calculate_collection(my_bgg_data.user_collection, my_bgg_data.game_info_db, my_bgg_data.play_no_db,
                                    st.session_state.toggle_owned, st.session_state.toggle_expansion, player_range)

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
