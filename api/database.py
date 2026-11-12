from sqlmodel import Field, Session, SQLModel, UniqueConstraint, create_engine

DATABASE_URL = 'sqlite:///movies.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(unique=True, index=True)
    title: str = Field(index=True)
    tags: str

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)

#one row = one user's stars for one movie. a user can have many ratings, but only one per movie
class Rating(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('user_id', 'movie_id'),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id', index=True)
    movie_id: int = Field(foreign_key='movie.movie_id', index=True)
    stars: int

def create_tables():
    SQLModel.metadata.create_all(engine)

#we have each sesson for each request per user when they wanna update data
def get_session():
    with Session(engine) as session:
        yield session
