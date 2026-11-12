import pytest

from tests.conftest import FAKE_POSTER


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'movies_loaded': 4800}


def test_list_movies_default(client):
    data = client.get('/movies').json()
    assert data['total'] == 4800
    assert len(data['results']) == 10
    assert data['results'][0] == {'movie_id': 19995, 'title': 'Avatar'}


def test_search_ignores_capitals(client):
    lower = client.get('/movies', params={'search': 'bat'}).json()
    upper = client.get('/movies', params={'search': 'BAT'}).json()
    assert lower['total'] == 26
    assert lower == upper


def test_search_pages(client):
    page_1 = client.get('/movies', params={'search': 'bat', 'limit': 5}).json()
    page_2 = client.get('/movies', params={'search': 'bat', 'limit': 5, 'offset': 5}).json()
    assert page_2['results'][0]['title'] == 'Batman & Robin'
    assert page_1['results'] != page_2['results']


def test_search_with_no_matches(client):
    data = client.get('/movies', params={'search': 'zzzz'}).json()
    assert data == {'total': 0, 'results': []}


@pytest.mark.parametrize('limit', [0, 51])
def test_limit_out_of_range(client, limit):
    response = client.get('/movies', params={'limit': limit})
    assert response.status_code == 422


def test_get_movie(client):
    response = client.get('/movies/272')
    assert response.status_code == 200
    movie = response.json()
    assert movie['title'] == 'Batman Begins'
    assert movie['poster'] == FAKE_POSTER


def test_get_movie_not_found(client):
    response = client.get('/movies/999999')
    assert response.status_code == 404
    assert response.json() == {'detail': 'Movie 999999 not found'}


def test_recommendations(client):
    data = client.get('/movies/272/recommendations').json()
    recommendations = data['recommendations']
    assert data['title'] == 'Batman Begins'
    assert len(recommendations) == 5
    assert recommendations[0]['title'] == 'The Dark Knight'
    assert 272 not in [movie['movie_id'] for movie in recommendations]

    scores = [movie['score'] for movie in recommendations]
    assert scores == sorted(scores, reverse=True)


def test_recommendations_k(client):
    data = client.get('/movies/272/recommendations', params={'k': 3}).json()
    assert len(data['recommendations']) == 3


def test_recommendations_not_found(client):
    response = client.get('/movies/999999/recommendations')
    assert response.status_code == 404
