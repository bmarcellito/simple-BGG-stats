from time import sleep
import gc


def extra_admin() -> None:
    while True:
        print(f'Garbage col: {gc.get_count()}')
        gc.collect()
        sleep(60*10)
    # if bgg_username == "bmarcell":
    #     with st.expander("See logs"):
    #         st.markdown(f'Garbage col: {gc.get_count()}')
