import os
import requests
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
FALLBACK_POSTER = 'https://placehold.co/500x750?text=No+Poster'

poster_cache = {}

def get_poster(movie_id):
    if movie_id in poster_cache:
        return poster_cache[movie_id]

    url = f'https://api.themoviedb.org/3/movie/{movie_id}'
    try:
        response = requests.get(url, params={'api_key': TMDB_API_KEY}, timeout=5)
        response.raise_for_status()
        poster_path = response.json().get('poster_path')
    except requests.RequestException:
        return FALLBACK_POSTER

    if poster_path:
        poster = f'https://image.tmdb.org/t/p/w500{poster_path}'
    else:
        poster = FALLBACK_POSTER

    poster_cache[movie_id] = poster
    return poster
