import pandas as pd
from sqlalchemy import insert
from sqlmodel import Session, SQLModel, col, delete, select

from api.database import Movie, Rating, User, engine

ML_FOLDER = 'data/ml-latest-small'
PREFIX = 'movielens_'


#MovieLens uses half stars (0.5 - 5.0), we use whole stars (1 - 5). round halves up
def to_stars(rating):
    return int(rating + 0.5)


def import_movielens(db_engine=engine, folder=ML_FOLDER):
    SQLModel.metadata.create_all(db_engine)

    #1. read the files and swap MovieLens movie ids for TMDB ids (our movie_id)
    links = pd.read_csv(f'{folder}/links.csv').dropna(subset=['tmdbId'])
    ratings = pd.read_csv(f'{folder}/ratings.csv')
    ratings = ratings.merge(links[['movieId', 'tmdbId']], on='movieId')
    ratings['tmdbId'] = ratings['tmdbId'].astype(int)

    with Session(db_engine) as session:
        #2. keep only ratings for movies we have
        our_movie_ids = set(session.exec(select(Movie.movie_id)).all())
        ratings = ratings[ratings['tmdbId'].isin(our_movie_ids)]
        ratings = ratings.drop_duplicates(['userId', 'tmdbId'], keep='last')

        #3. remove an earlier import, so running this twice gives the same result
        old_user_ids = select(User.id).where(col(User.username).startswith(PREFIX))
        session.exec(delete(Rating).where(col(Rating.user_id).in_(old_user_ids)))
        session.exec(delete(User).where(col(User.username).startswith(PREFIX)))

        #4. one user in our database for each MovieLens user
        users = [User(username=f'{PREFIX}{ml_id}') for ml_id in sorted(ratings['userId'].unique())]
        session.add_all(users)
        session.flush()
        user_ids = {user.username: user.id for user in users}

        #5. all ratings in one bulk insert
        rows = [
            {'user_id': user_ids[f'{PREFIX}{row.userId}'], 'movie_id': int(row.tmdbId), 'stars': to_stars(row.rating)}
            for row in ratings.itertuples()
        ]
        session.exec(insert(Rating), params=rows)
        session.commit()

    print('Imported', len(users), 'users and', len(rows), 'ratings')
    return {'users': len(users), 'ratings': len(rows)}


if __name__ == '__main__':
    import_movielens()
