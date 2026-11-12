import pickle
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from api.database import Movie, create_tables, get_session
from api.posters import get_poster
from api.recommender import recommend

data = {}

#server start -> immediately load data -> yield(...) -> only run lines after yield once server stops
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    data['movies'] = pickle.load(open('model/movie_list.pkl', 'rb'))
    data['similarity'] = pickle.load(open('model/similarity.pkl', 'rb'))
    print('Loaded', len(data['movies']), 'movies')
    yield
    data.clear()

app = FastAPI(title='Movie Recommender API', lifespan=lifespan) # creates app

#shapes of the request body for creating / updating a movie
class MovieCreate(SQLModel):
    movie_id: int
    title: str = Field(min_length=1)
    tags: str = ''

class MovieUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1)
    tags: str | None = None

#find one movie in the database, or stop with 404
def find_movie(session, movie_id):
    movie = session.exec(select(Movie).where(Movie.movie_id == movie_id)).first()
    if movie is None:
        raise HTTPException(status_code=404, detail=f'Movie {movie_id} not found')
    return movie

@app.get('/health') #endpoint ensuring server running
def health():
    return {'status': 'ok', 'movies_loaded': len(data['movies'])}

#search and list movies w some constraint (now reads from the database)
@app.get('/movies')
def list_movies(
    search: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    query = select(Movie).order_by(Movie.id)
    if search:
        query = query.where(Movie.title.contains(search))

    total = len(session.exec(query).all())
    page = session.exec(query.offset(offset).limit(limit)).all()
    return {
        'total': total,
        'results': [{'movie_id': movie.movie_id, 'title': movie.title} for movie in page],
    }

#get specifically a movie detail by its id (now reads from the database)
@app.get('/movies/{movie_id}')
def get_movie(movie_id: int, session: Session = Depends(get_session)):
    movie = find_movie(session, movie_id)
    result = movie.model_dump()
    result['poster'] = get_poster(movie_id)
    return result

#CREATE: add a new movie
@app.post('/movies', status_code=201)
def create_movie(new_movie: MovieCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Movie).where(Movie.movie_id == new_movie.movie_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f'Movie {new_movie.movie_id} already exists')

    movie = Movie.model_validate(new_movie)
    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie

#UPDATE: change only the fields that were sent
@app.patch('/movies/{movie_id}')
def update_movie(movie_id: int, changes: MovieUpdate, session: Session = Depends(get_session)):
    movie = find_movie(session, movie_id)
    movie.sqlmodel_update(changes.model_dump(exclude_none=True))
    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie

#DELETE: remove a movie
@app.delete('/movies/{movie_id}', status_code=204)
def delete_movie(movie_id: int, session: Session = Depends(get_session)):
    movie = find_movie(session, movie_id)
    session.delete(movie)
    session.commit()

class Recommendation(BaseModel):
    movie_id: int
    title: str
    score: float
    poster: str
class RecommendationResponse(BaseModel):
    movie_id: int
    title: str
    poster: str
    recommendations: list[Recommendation]

#recommend 5 movies
@app.get('/movies/{movie_id}/recommendations', response_model=RecommendationResponse)
def get_recommendations(movie_id: int, k: int = Query(5, ge=1, le=20), session: Session = Depends(get_session)):
    movie = get_movie(movie_id, session)
    if movie_id not in data['movies']['movie_id'].values:
        raise HTTPException(status_code=404, detail=f'No recommendations yet for movie {movie_id}')
    results = recommend(data['movies'], data['similarity'], movie_id, k)
    for movie_result in results:
        movie_result['poster'] = get_poster(movie_result['movie_id'])
    return {'movie_id': movie_id, 'title': movie['title'], 'poster': movie['poster'], 'recommendations': results}
