import pytest


def make_user(client, username):
    return client.post('/users', json={'username': username}).json()['id']


def test_create_user(client):
    response = client.post('/users', json={'username': 'quang'})
    assert response.status_code == 201
    assert response.json()['username'] == 'quang'
    assert response.json()['id'] is not None


def test_username_taken(client):
    client.post('/users', json={'username': 'alice'})
    response = client.post('/users', json={'username': 'alice'})
    assert response.status_code == 409


@pytest.mark.parametrize('username', ['ab', 'x' * 31])
def test_username_bad_length(client, username):
    response = client.post('/users', json={'username': username})
    assert response.status_code == 422


def test_get_user(client):
    user_id = make_user(client, 'bob')
    response = client.get(f'/users/{user_id}')
    assert response.status_code == 200
    assert response.json()['username'] == 'bob'


def test_get_missing_user(client):
    response = client.get('/users/999999')
    assert response.status_code == 404


def test_new_user_has_no_ratings(client):
    user_id = make_user(client, 'carol')
    assert client.get(f'/users/{user_id}/ratings').json() == []


def test_rate_movies(client):
    user_id = make_user(client, 'dave')
    response = client.put(f'/users/{user_id}/ratings/272', json={'stars': 5})
    assert response.status_code == 200
    assert response.json() == {'user_id': user_id, 'movie_id': 272, 'title': 'Batman Begins', 'stars': 5}

    client.put(f'/users/{user_id}/ratings/19995', json={'stars': 3})
    ratings = client.get(f'/users/{user_id}/ratings').json()
    assert ratings == [
        {'movie_id': 272, 'title': 'Batman Begins', 'stars': 5},
        {'movie_id': 19995, 'title': 'Avatar', 'stars': 3},
    ]


def test_rate_same_movie_again_changes_it(client):
    user_id = make_user(client, 'erin')
    client.put(f'/users/{user_id}/ratings/272', json={'stars': 2})
    client.put(f'/users/{user_id}/ratings/272', json={'stars': 4})

    ratings = client.get(f'/users/{user_id}/ratings').json()
    assert len(ratings) == 1
    assert ratings[0]['stars'] == 4


def test_ratings_are_per_user(client):
    frank = make_user(client, 'frank')
    grace = make_user(client, 'grace')
    client.put(f'/users/{frank}/ratings/272', json={'stars': 5})

    assert len(client.get(f'/users/{frank}/ratings').json()) == 1
    assert client.get(f'/users/{grace}/ratings').json() == []


@pytest.mark.parametrize('stars', [0, 6])
def test_stars_out_of_range(client, stars):
    user_id = make_user(client, f'stars{stars}')
    response = client.put(f'/users/{user_id}/ratings/272', json={'stars': stars})
    assert response.status_code == 422


def test_rate_missing_movie(client):
    user_id = make_user(client, 'henry')
    response = client.put(f'/users/{user_id}/ratings/999999', json={'stars': 4})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Movie 999999 not found'}


def test_rate_as_missing_user(client):
    response = client.put('/users/999999/ratings/272', json={'stars': 4})
    assert response.status_code == 404
    assert response.json() == {'detail': 'User 999999 not found'}
