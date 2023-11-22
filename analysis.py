import pandas as pd
from compute_elo import run_matches

def get_corr(df):
    return df['difficulty_num'].corr(df['elo_rating'])

def plot(df):
    df.plot(x='difficulty_num', y='elo_rating', kind='scatter')