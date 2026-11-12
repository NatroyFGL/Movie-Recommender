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


def test_new_movie_has_no_recommendations_yet(client):
    client.post('/movies', json={'movie_id': 999004, 'title': 'Brand New'})
    response = client.get('/movies/999004/recommendations')
    assert response.status_code == 404
    assert response.json() == {'detail': 'No recommendations yet for movie 999004'}
