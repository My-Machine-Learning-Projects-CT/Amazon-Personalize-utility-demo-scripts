import pandas as pd
from datetime import datetime
import locale

locale.setlocale(locale.LC_ALL, '')

interactions_df = None
movies_df = None

def load_interactions():
    print('Loading interaction data...')
    global interactions_df
    interactions_df = pd.read_csv('interactions.csv')
    print(f'Successfully loaded {interactions_df.shape[0]:n} interactions')

def load_movies():
    print('Loading movie data...')
    global movies_df
    movies_df = pd.read_csv('movies.csv', encoding='latin-1', dtype={'movieId': 'object', 'title': 'str', 'genres': 'str'}, index_col=0)
    print(f'Successfully loaded {movies_df.shape[0]:n} movies')

def lookup_movie_title_and_genres(item_id):
    movie = movies_df.loc[int(item_id)]
    return movie['title'], movie['genres']

def get_random_user_ids(num = 1):
    user_ids_df = pd.DataFrame(interactions_df['USER_ID'].unique())
    users = user_ids_df.sample(num)
    return users.index.tolist()

def get_random_movie_ids(num = 1):
    random_movies = movies_df.sample(num)
    return random_movies.index.tolist()

def get_interactions_for_user(user_id):
    user_interactions_df = interactions_df.loc[interactions_df['USER_ID'] == int(user_id)]
    user_interactions_df = user_interactions_df.drop_duplicates(subset=['ITEM_ID'])
    user_interactions_df = user_interactions_df.sort_values(by='TIMESTAMP', ascending=False)
    user_interactions_df['TITLE'] = user_interactions_df.apply(lambda row: lookup_movie_title_and_genres(row['ITEM_ID'])[0], axis=1)
    user_interactions_df['GENRES'] = user_interactions_df.apply(lambda row: lookup_movie_title_and_genres(row['ITEM_ID'])[1], axis=1)
    user_interactions_df['DATE'] = user_interactions_df.apply(lambda row: datetime.utcfromtimestamp(int(row['TIMESTAMP'])), axis=1)
    return user_interactions_df.drop(['USER_ID', 'TIMESTAMP'], axis=1)

def expand_genres(df):
    parsed_genres = [] 
    for genres in df['GENRES'].tolist():
        parsed_genres.extend(genres.split('|'))

    genres_df = pd.DataFrame(parsed_genres)
    genres_df.columns = ['GENRE']
    return genres_df

def get_popular_genres(df, top_n = 20):
    genres_df = expand_genres(df)
    top_df = genres_df.value_counts().rename_axis('unique_values').reset_index(name='counts')
    return top_df.head(top_n)
