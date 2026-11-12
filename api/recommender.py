import numpy as np

def recommend(movies, similarity, movie_id, k):
    index = movies.index[movies['movie_id'] == movie_id][0]                       
    scores = sorted(enumerate(similarity[index]), reverse=True, key=lambda x: x[1])   

    results = []
    for position, score in scores[1:k + 1]:                                    
        row = movies.iloc[position]
        results.append({
            'movie_id': int(row['movie_id']),
            'title': row['title'],
            'score': round(float(score), 3),
        })
    return results

#personal recommendations: mix the similarity rows of every movie the user rated
def recommend_for_user(movies, similarity, stars_by_movie, k):
    positions = {movie_id: position for position, movie_id in enumerate(movies['movie_id'])}
    rated = [(positions[movie_id], stars) for movie_id, stars in stars_by_movie.items() if movie_id in positions]

    if not any(stars >= 4 for position, stars in rated):
        return []

    scores = np.zeros(len(movies))
    for position, stars in rated:
        scores += (stars - 3) * similarity[position]
    for position, stars in rated:
        scores[position] = -np.inf

    results = []
    for position in np.argsort(-scores, kind='stable')[:k]:
        row = movies.iloc[position]
        results.append({
            'movie_id': int(row['movie_id']),
            'title': row['title'],
            'score': round(float(scores[position]), 3),
        })
    return results
