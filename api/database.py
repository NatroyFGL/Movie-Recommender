from sqlmodel import Field, Session, SQLModel, create_engine

DATABASE_URL = 'sqlite:///movies.db'
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(unique=True, index=True)
    title: str = Field(index=True)
    tags: str

def create_tables():
    SQLModel.metadata.create_all(engine)

#we have each sesson for each request per user when they wanna update data
def get_session():
    with Session(engine) as session:
        yield session