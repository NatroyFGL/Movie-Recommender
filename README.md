Movie Recommender System

This is a simple movie recommender. You pick a movie you like, and it shows you 5 similar movies along with their posters.

How it works

The recommendations are based on the TMDB 5000 Movies dataset from Kaggle. For each movie, the notebook combines its overview, genres, keywords, top 3 cast members and director into one block of text. It then turns that text into word counts and measures how similar every movie is to every other movie using cosine similarity. When you choose a movie, the app returns the 5 movies with the highest similarity score. Posters are loaded from the TMDB website.

Files

app.py - the Streamlit web app.
notebook86c26b4f17.ipynb - the notebook that cleans the data and builds the model.

Setup

1. Install Python 3 and the needed packages:

   pip install streamlit requests pandas numpy scikit-learn

2. Download the TMDB 5000 Movie dataset from Kaggle (tmdb_5000_movies.csv and tmdb_5000_credits.csv).

3. Run the notebook. At the end it creates two files: movie_list.pkl and similarity.pkl.

4. Make a folder called model next to app.py and put both .pkl files inside it.

5. Start the app:

   streamlit run app.py

6. Your browser will open the app. Choose a movie from the list and click "Show Recommendation".

Notes

You need an internet connection for the posters to load.
The similarity.pkl file can be large, since it stores a score for every pair of movies.
