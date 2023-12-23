import pandas as pd
import streamlit as st


def stat_not_played(df_collection: pd.DataFrame) -> None:
    # st.subheader("Owned games not played yet")
    games_owned = df_collection.loc[df_collection["own"] == 1]
    not_played = pd.DataFrame(games_owned["name"].loc[games_owned["numplays"] == 0].sort_values())
    if not_played.empty:
        st.write("Congratulation, you have already played with all games you currently own!")
    else:
        not_played.index = pd.RangeIndex(start=1, stop=len(not_played) + 1, step=1)
        st.table(not_played)
