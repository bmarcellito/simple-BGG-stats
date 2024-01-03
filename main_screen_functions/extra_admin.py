import streamlit as st

if st.secrets["environment"] == "dev":
    from time import sleep
    import gc
    import sys
    from my_logger import logger


def extra_admin() -> None:
    if st.secrets["environment"] == "dev":
        ph_admin = st.empty()
        while True:
            with ph_admin.container():
                # logger.info(f'Garbage col: {gc.get_count()}')
                st.write(f'Amount of variables before garbage collection: {gc.get_count()}')
                # gc.collect()
                # st.write(f'Amount of variables after garbage collection: {gc.get_count()}')
                if "my_collection" in st.session_state:
                    st.write(f'Size of my_collection: {sys.getsizeof(st.session_state.my_collection)}')
                if "my_plays" in st.session_state:
                    st.write(f'Size of my_plays: {sys.getsizeof(st.session_state.my_plays)}')
                st.write(st.session_state)
            sleep(60*30)
            ph_admin.empty()
