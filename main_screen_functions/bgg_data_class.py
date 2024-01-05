import pandas as pd


class BggData:
    def __init__(self):
        self.username_cache = pd.DataFrame()
        self.user_collection = pd.DataFrame()
        self.user_plays = pd.DataFrame()
        self.current_rankings = pd.DataFrame()
        self.historical_rankings = pd.DataFrame()
        self.game_info_db = pd.DataFrame()
        self.play_no_db = pd.DataFrame
