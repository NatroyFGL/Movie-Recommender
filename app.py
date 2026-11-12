import os
import requests
import streamlit as st

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def api_get(path, params=None):
    try:
        response = requests.get(f'{API_URL}{path}', params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error(f'Could not reach the API at {API_URL}. Is it running?')
        st.stop()


st.header('Movie Recommender System')

search = st.text_input('Search for a movie', placeholder='e.g. batman')
movies = api_get('/movies', {'search': search, 'limit': 50})['results']

if not movies:
    st.warning('No movies found. Try another search.')
    st.stop()

selected = st.selectbox(
    'Pick a movie',
    movies,
    format_func=lambda movie: movie['title'],
)

if st.button('Show Recommendation'):
    with st.spinner('Finding similar movies...'):
        result = api_get(f"/movies/{selected['movie_id']}/recommendations", {'k': 5})

    columns = st.columns(5)
    for column, movie in zip(columns, result['recommendations']):
        with column:
            st.text(movie['title'])
            st.image(movie['poster'])
