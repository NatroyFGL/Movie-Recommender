import pickle

from sqlmodel import Session, SQLModel, delete, select
from api.database import Movie, engine

def seed(db_engine=engine):
    SQLModel.metadata.create_all(db_engine)
    movies = pickle.load(open('model/movie_list.pkl', 'rb'))
    #delete then refill
    with Session(db_engine) as session:
        session.exec(delete(Movie))
        for row in movies.itertuples():
            session.add(Movie(movie_id=int(row.movie_id), title=row.title, tags=row.tags))
        session.commit()

        count = len(session.exec(select(Movie)).all())
    print('Seeded', count, 'movies')


if __name__ == '__main__':
    seed()


