import pytest
from sqlmodel import Session, select

from api.database import User
from scripts.import_movielens import import_movielens, to_stars

#a tiny fake MovieLens: 2 users, 6 ratings
LINKS = """movieId,imdbId,tmdbId
1,1,272
2,2,19995
3,3,
4,4,999999
5,5,155
"""

RATINGS = """userId,movieId,rating,timestamp
1,1,5.0,0
1,2,3.5,0
1,3,4.0,0
1,4,4.0,0
2,2,0.5,0
2,5,4.5,0
"""


@pytest.fixture(scope='module')
def fake_movielens(tmp_path_factory):
    folder = tmp_path_factory.mktemp('movielens')
    (folder / 'links.csv').write_text(LINKS)
    (folder / 'ratings.csv').write_text(RATINGS)
    return folder


def user_id(test_engine, username):
    with Session(test_engine) as session:
        return session.exec(select(User).where(User.username == username)).first().id


@pytest.mark.parametrize('rating, stars', [(0.5, 1), (1.0, 1), (2.5, 3), (3.5, 4), (4.5, 5), (5.0, 5)])
def test_to_stars(rating, stars):
    assert to_stars(rating) == stars


def test_import_skips_movies_we_dont_have(test_engine, fake_movielens):
    summary = import_movielens(test_engine, fake_movielens)
    assert summary == {'users': 2, 'ratings': 4}


def test_imported_ratings(client, test_engine, fake_movielens):
    import_movielens(test_engine, fake_movielens)
    ratings = client.get(f'/users/{user_id(test_engine, "movielens_1")}/ratings').json()
    assert ratings == [
        {'movie_id': 272, 'title': 'Batman Begins', 'stars': 5},
        {'movie_id': 19995, 'title': 'Avatar', 'stars': 4},
    ]


def test_import_twice_gives_same_result(test_engine, fake_movielens):
    import_movielens(test_engine, fake_movielens)
    import_movielens(test_engine, fake_movielens)
    with Session(test_engine) as session:
        users = session.exec(select(User).where(User.username.startswith('movielens_'))).all()
    assert len(users) == 2


def test_import_keeps_other_users(client, test_engine, fake_movielens):
    my_id = client.post('/users', json={'username': 'quang'}).json()['id']
    client.put(f'/users/{my_id}/ratings/272', json={'stars': 5})

    import_movielens(test_engine, fake_movielens)
    assert len(client.get(f'/users/{my_id}/ratings').json()) == 1


def test_imported_user_gets_for_you(client, test_engine, fake_movielens):
    import_movielens(test_engine, fake_movielens)
    data = client.get(f'/users/{user_id(test_engine, "movielens_2")}/for-you').json()
    recommended = [movie['movie_id'] for movie in data['recommendations']]
    assert data['based_on'] == 2
    assert len(recommended) > 0
    assert 19995 not in recommended and 155 not in recommended
