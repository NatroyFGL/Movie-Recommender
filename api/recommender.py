import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize


#turn every movie's tags into a vector, once. replaces the old 184 MB similarity.pkl
def build_index(movies):
    vectorizer = CountVectorizer(max_features=5000, stop_words='english')
    vectors = normalize(vectorizer.fit_transform([movie.tags for movie in movies]))
    return {
        'movie_ids': [movie.movie_id for movie in movies],
        'titles': [movie.title for movie in movies],
        'positions': {movie.movie_id: position for position, movie in enumerate(movies)},
        'vectors': vectors,
    }


#weights says how much each movie counts. returns one match score per movie
def match_scores(index, weights):
    taste = index['vectors'].T @ weights
    return index['vectors'] @ taste


#best k movies, skipping the ones in exclude and anything with no match at all
def top_k(index, scores, exclude, k):
    scores = scores.copy()
    scores[exclude] = -np.inf

    results = []
    for position in np.argsort(-scores, kind='stable')[:k]:
        if scores[position] <= 0:
            break
        results.append({
            'movie_id': index['movie_ids'][position],
            'title': index['titles'][position],
            'score': round(float(scores[position]), 3),
        })
    return results


#movies similar to one movie
def recommend(index, movie_id, k):
    position = index['positions'][movie_id]
    weights = np.zeros(len(index['movie_ids']))
    weights[position] = 1
    return top_k(index, match_scores(index, weights), [position], k)


#personal recommendations: liked movies (4-5 stars) pull, disliked ones (1-2 stars) push
def recommend_for_user(index, stars_by_movie, k):
    weights = np.zeros(len(index['movie_ids']))
    rated = []
    for movie_id, stars in stars_by_movie.items():
        if movie_id in index['positions']:
            position = index['positions'][movie_id]
            weights[position] = stars - 3
            rated.append(position)
    return top_k(index, match_scores(index, weights), rated, k)
