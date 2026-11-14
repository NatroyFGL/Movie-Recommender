NEW_MOVIE = {'movie_id': 999001, 'title': 'My Test Movie', 'tags': 'space robots friendship'}


def test_create_movie(client):
    response = client.post('/movies', json=NEW_MOVIE)
    assert response.status_code == 201
    assert response.json()['title'] == 'My Test Movie'

    assert client.get('/movies/999001').status_code == 200
    assert client.get('/movies', params={'search': 'My Test Movie'}).json()['total'] == 1


def test_create_duplicate_movie(client):
    response = client.post('/movies', json={'movie_id': 272, 'title': 'Batman Again'})
    assert response.status_code == 409


def test_create_movie_with_empty_title(client):
    response = client.post('/movies', json={'movie_id': 999002, 'title': ''})
    assert response.status_code == 422


def test_update_title_only(client):
    old_tags = client.get('/movies/272').json()['tags']

    response = client.patch('/movies/272', json={'title': 'Batman Begins (2005)'})
    assert response.status_code == 200
    assert response.json()['title'] == 'Batman Begins (2005)'
    assert response.json()['tags'] == old_tags


def test_update_missing_movie(client):
    response = client.patch('/movies/999999', json={'title': 'Nope'})
    assert response.status_code == 404


def test_delete_movie(client):
    client.post('/movies', json={'movie_id': 999003, 'title': 'Delete Me'})

    response = client.delete('/movies/999003')
    assert response.status_code == 204
    assert client.get('/movies/999003').status_code == 404


def test_delete_missing_movie(client):
    response = client.delete('/movies/999999')
    assert response.status_code == 404


def test_new_movie_gets_recommendations(client):
    client.post('/movies', json={'movie_id': 999004, 'title': 'Brand New', 'tags': 'batman gotham joker wayne'})
    response = client.get('/movies/999004/recommendations')
    assert response.status_code == 200
    titles = [movie['title'] for movie in response.json()['recommendations']]
    assert 'The Dark Knight' in titles


def test_new_movie_shows_up_in_other_recommendations(client):
    tags = client.get('/movies/272').json()['tags']
    client.post('/movies', json={'movie_id': 999005, 'title': 'Batman Begins Copy', 'tags': tags})
    data = client.get('/movies/272/recommendations').json()
    assert data['recommendations'][0]['title'] == 'Batman Begins Copy'


def test_movie_without_tags_gets_empty_recommendations(client):
    client.post('/movies', json={'movie_id': 999006, 'title': 'No Tags'})
    response = client.get('/movies/999006/recommendations')
    assert response.status_code == 200
    assert response.json()['recommendations'] == []


def test_deleted_movie_is_never_recommended(client):
    client.delete('/movies/155')
    data = client.get('/movies/272/recommendations', params={'k': 20}).json()
    assert 155 not in [movie['movie_id'] for movie in data['recommendations']]

