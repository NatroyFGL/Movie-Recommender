def make_user_with_ratings(client, username, stars_by_movie):
    user_id = client.post('/users', json={'username': username}).json()['id']
    for movie_id, stars in stars_by_movie.items():
        client.put(f'/users/{user_id}/ratings/{movie_id}', json={'stars': stars})
    return user_id


def titles(data):
    return [movie['title'] for movie in data['recommendations']]


def test_no_ratings_gives_empty_list(client):
    user_id = make_user_with_ratings(client, 'newbie', {})
    data = client.get(f'/users/{user_id}/for-you').json()
    assert data == {'user_id': user_id, 'username': 'newbie', 'based_on': 0, 'recommendations': []}


def test_one_loved_movie_matches_movie_recommendations(client):
    user_id = make_user_with_ratings(client, 'batfan', {272: 5})
    for_you = client.get(f'/users/{user_id}/for-you', params={'k': 5}).json()
    similar = client.get('/movies/272/recommendations', params={'k': 5}).json()
    assert titles(for_you) == titles(similar)


def test_rated_movies_are_not_recommended(client):
    user_id = make_user_with_ratings(client, 'seenit', {272: 5, 155: 4})
    data = client.get(f'/users/{user_id}/for-you', params={'k': 20}).json()
    recommended_ids = [movie['movie_id'] for movie in data['recommendations']]
    assert 272 not in recommended_ids
    assert 155 not in recommended_ids
    assert data['based_on'] == 2


def test_two_loved_movies_mix_both(client):
    user_id = make_user_with_ratings(client, 'mixer', {272: 5, 19995: 5})
    data = client.get(f'/users/{user_id}/for-you', params={'k': 5}).json()
    assert titles(data)[0] == 'The Dark Knight'
    assert 'Batman v Superman: Dawn of Justice' in titles(data)


def test_only_dislikes_gives_empty_list(client):
    user_id = make_user_with_ratings(client, 'grumpy', {272: 2, 155: 1})
    data = client.get(f'/users/{user_id}/for-you').json()
    assert data['recommendations'] == []


def test_scores_are_sorted(client):
    user_id = make_user_with_ratings(client, 'sorted', {272: 5, 19995: 4})
    scores = [movie['score'] for movie in client.get(f'/users/{user_id}/for-you').json()['recommendations']]
    assert len(scores) == 10
    assert scores == sorted(scores, reverse=True)


def test_k(client):
    user_id = make_user_with_ratings(client, 'kuser', {272: 5})
    data = client.get(f'/users/{user_id}/for-you', params={'k': 3}).json()
    assert len(data['recommendations']) == 3


def test_for_you_missing_user(client):
    response = client.get('/users/999999/for-you')
    assert response.status_code == 404
