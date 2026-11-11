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