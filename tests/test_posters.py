import pytest
import requests

from api import posters


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


@pytest.fixture(autouse=True)
def empty_cache():
    posters.poster_cache.clear()


def test_builds_full_poster_link(monkeypatch):
    monkeypatch.setattr(posters.requests, 'get', lambda *args, **kwargs: FakeResponse({'poster_path': '/abc.jpg'}))
    assert posters.get_poster(155) == 'https://image.tmdb.org/t/p/w500/abc.jpg'


def test_second_call_uses_cache(monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return FakeResponse({'poster_path': '/abc.jpg'})

    monkeypatch.setattr(posters.requests, 'get', fake_get)
    posters.get_poster(155)
    posters.get_poster(155)
    assert len(calls) == 1


def test_movie_without_poster_gets_fallback(monkeypatch):
    monkeypatch.setattr(posters.requests, 'get', lambda *args, **kwargs: FakeResponse({'poster_path': None}))
    assert posters.get_poster(155) == posters.FALLBACK_POSTER


def test_tmdb_down_gets_fallback_and_is_not_cached(monkeypatch):
    def broken_get(*args, **kwargs):
        raise requests.ConnectionError('TMDB is down')

    monkeypatch.setattr(posters.requests, 'get', broken_get)
    assert posters.get_poster(155) == posters.FALLBACK_POSTER
    assert 155 not in posters.poster_cache
