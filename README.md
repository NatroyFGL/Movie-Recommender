### Movie Recommender System

This is a simple movie recommender. You pick a movie you like, and it shows you 5 similar movies along with their posters.

### How it works

The recommendations are based on the TMDB 5000 Movies dataset from Kaggle. For each movie, the notebook combines its overview, genres, keywords, top 3 cast members and director into one block of text. It then turns that text into word counts and measures how similar every movie is to every other movie using cosine similarity. When you choose a movie, the app returns the 5 movies with the highest similarity score. Posters are loaded from the TMDB website.

### Architecture map
![Uploading image.png…]()


Files

app.py - the Streamlit web app.
notebooks/main.ipynb - the notebook that cleans the data and builds the model.
data/ - the dataset CSV files (not uploaded to GitHub).
model/ - the files the notebook builds (not uploaded to GitHub).
requirements.txt - the Python packages the project needs.
.env.example - shows which secret settings the app needs.

Setup

1. Install Python 3 and the needed packages:

   pip install -r requirements.txt

2. Download the TMDB 5000 Movie dataset from Kaggle (https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata). Put tmdb_5000_movies.csv and tmdb_5000_credits.csv in the data folder.

3. Get a free API key from TMDB (https://www.themoviedb.org/settings/api). Make a copy of .env.example, name it .env, and put your key in it.

4. Run every cell in notebooks/main.ipynb. At the end it saves movie_list.pkl and similarity.pkl in the model folder.

5. Start the app from the main project folder:

   streamlit run app.py

6. Your browser will open the app. Choose a movie from the list and click "Show Recommendation".

Notes

You need an internet connection for the posters to load.
The similarity.pkl file is about 184 MB, since it stores a score for every pair of movies.
Never upload your .env file. It holds your private API key.
