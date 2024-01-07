from threading import Thread
from streamlit.runtime.scriptrunner import add_script_run_ctx

from bgg_import.get_functions import *
# from my_gdrive.save_functions.token_mgmt import maintain_tokens


def init_load() -> None:
    thread_current_ranking = Thread(target=get_current_rankings)
    thread_current_ranking.name = "init_current_ranking"
    add_script_run_ctx(thread_current_ranking)
    thread_current_ranking.start()

    thread_game_infodb = Thread(target=get_game_infodb)
    thread_game_infodb.name = "init_game_infodb"
    add_script_run_ctx(thread_game_infodb)
    thread_game_infodb.start()

    thread_historic_ranking = Thread(target=get_historic_rankings)
    thread_historic_ranking.name = "init_historic_ranking"
    add_script_run_ctx(thread_historic_ranking)
    thread_historic_ranking.start()

    thread_play_numdb = Thread(target=get_play_no_db)
    thread_play_numdb.name = "init_play_no_db"
    add_script_run_ctx(thread_play_numdb)
    thread_play_numdb.start()

    thread_user_cache = Thread(target=get_username_cache)
    thread_user_cache.name = "init_username_cache"
    add_script_run_ctx(thread_user_cache)
    thread_user_cache.start()

    # thread_maintain_tokens = Thread(target=maintain_tokens)
    # thread_maintain_tokens.name = "maintain_tokens"
    # add_script_run_ctx(thread_maintain_tokens)
    # thread_maintain_tokens.start()
    return None
