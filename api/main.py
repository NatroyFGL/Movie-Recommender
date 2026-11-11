import pickle
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from api.recommender import recommend

data = {}

#server start -> immediately load data -> yield(server running and handle request) -> only run 
#lines after yield once server stops(clear data for memory saving)
@asynccontextmanager
async def lifespan(app: FastAPI):
    data['movies'] = pickle.load(open('model/movie_list.pkl', 'rb'))
    data['similarity'] = pickle.load(open('model/similarity.pkl', 'rb'))
    print('Loaded', len(data['movies']), 'movies')
    yield
    data.clear()

app = FastAPI(title='Movie Recommender API', lifespan=lifespan) # creates app

@app.get('/health') #endpoint ensuring server running
def health():
    return {'status': 'ok', 'movies_loaded': len(data['movies'])}

#search and list movies w some constraint
@app.get('/movies')
def list_movies(
    search: str | None = None,
    limit: int = Query(10, ge=1, le=50),   
    offset: int = Query(0, ge=0),           
):
    movies = data['movies']

    if search:                                      
        matches = movies['title'].str.contains(search, case=False, regex=False)   
        movies = movies[matches]                     

    total = len(movies)                             
    page = movies.iloc[offset : offset + limit]               

    return {
        'total': total,                            
        'results': page[['movie_id', 'title']].to_dict('records'),   
    }

#get specifically a movie detail by its id
@app.get('/movies/{movie_id}')                        
def get_movie(movie_id: int):                    
    movies = data['movies']
    match = movies[movies['movie_id'] == movie_id]    

    if match.empty:                                
        raise HTTPException(status_code=404, detail=f'Movie {movie_id} not found')  

    return match.iloc[0].to_dict()             

class Recommendation(BaseModel):
    movie_id: int
    title: str
    score: float


class RecommendationResponse(BaseModel):
    movie_id: int
    title: str
    recommendations: list[Recommendation]

@app.get('/movies/{movie_id}/recommendations', response_model=RecommendationResponse)
def get_recommendations(movie_id: int, k: int = Query(5, ge=1, le=20)):
    movie = get_movie(movie_id)
    results = recommend(data['movies'], data['similarity'], movie_id, k)
    return {'movie_id': movie_id, 'title': movie['title'], 'recommendations': results}