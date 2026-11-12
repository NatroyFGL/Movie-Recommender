### app run
& "$env:USERPROFILE\.conda\envs\anaconda-2025.12-py3.13\python.exe" -m uvicorn api.main:app --reload
### Overall
Where you are now
Notebook → .pkl files → Streamlit app. It works, but it has three limits:

It doesn't scale: the similarity table stores a score for every pair of movies. 4,800 movies needs 184 MB, and 45,000 movies would need about 16 GB.
It isn't personal: everyone who picks Batman gets the same 5 movies.
It only matches words: it can't tell that "a heist gone wrong" and "a robbery that fails" mean the same thing.
The steps below fix these one at a time.

### Phase 0: Tidy up (1 session)
Step	What you build	What you learn
0	Folders (api/, notebooks/, model/), a requirements.txt, a .gitignore, and your API key moved into a .env file	Project structure, keeping secrets out of code
Done when: the repo pushes to GitHub without the 184 MB file or your API key.

### Phase 1: FastAPI backend (uses what you already know)
The goal is to split the project into a backend, which does the work, and a frontend, which shows it.

Step	What you build	What you learn
1	GET /health and GET /movies?search=bat&limit=10, with the .pkl files loaded once when the server starts	Startup loading, query parameters, pagination
2	GET /movies/{movie_id}, which returns 404 if the movie doesn't exist	Path parameters, error handling
3	GET /movies/{movie_id}/recommendations?k=5, with the logic moved into recommender.py	Separating logic from routes, Pydantic response models
4	Posters fetched through the API, saved after the first fetch, with a fallback image when TMDB has none	Calling other APIs, caching, handling missing data
5	Streamlit calls your API instead of opening the .pkl files	How a frontend and backend talk to each other
6	Tests with pytest and FastAPI's TestClient	Testing endpoints automatically
Using movie_id instead of the title also fixes the two-Batmans problem.

### Phase 2: A database, users and ratings (your CRUD skills)
Step	What you build	What you learn
7	SQLite with SQLModel, loading the movies from the CSV into a table, plus CRUD endpoints for movies	Databases, ORMs, migrations
8	POST /users, plus endpoints for users to rate movies and see their ratings	Table relationships (one user has many ratings)
9	GET /users/{id}/for-you, which combines the movies a user liked to find new ones	Your first personal recommendations

### Phase 3: Make it scale
Step	What you build	What you learn
10	Remove similarity.pkl and calculate only the top matches when someone asks	Why storing every pair can't scale
11	A bigger dataset (MovieLens, which has about 87,000 movies and millions of real ratings)	Joining datasets with links.csv, which matches MovieLens IDs to TMDB IDs
12	Docker and docker-compose, then switching from SQLite to Postgres	Running the project the same way on any computer

### Phase 4: Smarter ML
Before making it "smarter", you need a way to measure it. Otherwise "smarter" is just a feeling.
Step	What you build	What you learn
13	An evaluation script: hide some of each user's ratings, see if the model recommends those movies, and score it (hit rate, precision@10)	Train/test splits, metrics
14	TF-IDF instead of CountVectorizer, with the before and after scores compared	Feature engineering backed by evidence
15	Collaborative filtering ("people who liked X also liked Y") with matrix factorization	Learning from behaviour instead of descriptions
16	A hybrid: use content matching for new users and ratings for active ones, then compare scores	The cold start problem, blending models
17	Experiment tracking in MLflow	Keeping track of which version won

### Phase 5: Neural networks
Step	What you build	What you learn
18	Sentence embeddings from a ready-made model like all-MiniLM-L6-v2 for each movie's overview, then compare the score with Step 14	Embeddings, which capture meaning rather than words
19	FAISS for fast similarity search	Vector search across a huge number of items
20	Your own two-tower model in PyTorch (one network for users, one for movies), trained on MovieLens	Building and training a neural network

### Phase 6: RAG (ties into your other project)
Step	What you build	What you learn
21	POST /search with a request like "a sad space movie about a father and daughter": turn the query into an embedding, find matches in FAISS and return them	Semantic search
22	An LLM ranks those matches and explains each pick using the plot summary ("because you liked…")	Retrieval plus generation, keeping answers grounded
23	A chat page in the frontend	Putting it all together

### Phase 7: Optional extras
Logins with JWT
Redis caching
Background jobs to retrain the model
Deploying online (Render, Railway or Hugging Face Spaces)
How we'll work
One step at a time: I explain the idea first, you write the code, and I review it. I won't hand you a finished version.
One commit per step: that way you can always go back.
Don't skip Step 13: "I made it smarter, and here's the number that proves it" is what makes this stand out on a resume.
Ready for Step 0? Since it's mostly tidying, I can do it with you in about 10 minutes, then we'll start your first FastAPI endpoint in Step 1. I can also turn this roadmap into a checklist page you can tick off as you go.












### Step 1 backend fastapi detailed
Step 1: Your first API endpoints
The big idea
Right now, app.py does two jobs: it finds recommendations and it shows the page. We're going to split those jobs:


Before:  Streamlit app ──> opens the .pkl files directly

After:   Streamlit app ──HTTP──> FastAPI ──> opens the .pkl files
         (frontend: shows)        (backend: does the work)
Why bother? Once there's an API, anything can use your recommender, like a website, a phone app or another program, not just Streamlit. Real apps are built this way.

What's new for you in this step: loading data once at startup. similarity.pkl takes a few seconds to load. If every request loaded it again, every click would take seconds. So we load it once when the server starts, keep it in memory, and every request reuses it.

Part A: The starter code (I give you this)
Create a folder called api in the Movie folder, add a file called main.py inside it, and type this in. Typing it yourself helps it stick better than pasting.


import pickle
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query

data = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    data['movies'] = pickle.load(open('model/movie_list.pkl', 'rb'))
    print('Loaded', len(data['movies']), 'movies')
    yield
    data.clear()


app = FastAPI(title='Movie Recommender API', lifespan=lifespan)


@app.get('/health')
def health():
    return {'status': 'ok', 'movies_loaded': len(data['movies'])}
Block 1: imports. You know pickle. asynccontextmanager is the tool for startup code, and Query will be used in your task.

Block 2: data = {}. An empty dictionary, like a shelf where we'll keep the loaded data so every endpoint can reach it.

Block 3: lifespan. This is the startup and shutdown code. The yield splits it in two:


Code before yield  →  runs once when the server starts   (load the movies)
yield              →  the server runs and handles requests here
Code after yield   →  runs once when the server stops    (clean up)
So data['movies'] gets filled once, and then every request uses it. For now we only load the movie list. The similarity table comes in Step 3, when we need it.

Block 4: app = FastAPI(...). This creates the app and tells it to use our lifespan.

Block 5: /health. A simple endpoint that answers "is the server alive, and did the data load?" Real systems check this endpoint to see if a server is working.

Run it
In the Movie folder, run this in PowerShell:


& "$env:USERPROFILE\.conda\envs\anaconda-2025.12-py3.13\python.exe" -m uvicorn api.main:app --reload
api.main:app means "in the api folder, open main.py, and use the variable named app".
--reload restarts the server every time you save, which is handy while coding.
You should see Loaded 4800 movies. Then open:

http://localhost:8000/health, which should show {"status":"ok","movies_loaded":4800}.
http://localhost:8000/docs, a free test page FastAPI builds for you. You'll use it a lot.
Part B: Your task, GET /movies
Write this endpoint yourself, below /health.

It takes 3 query parameters:

Parameter	Default	Rule	What it does
search	none	optional	Only keep titles that contain this text, ignoring capitals
limit	10	between 1 and 50	How many movies to return
offset	0	0 or more	How many movies to skip (for pages)
It should return:


{
  "total": 26,
  "results": [
    {"movie_id": 209112, "title": "Batman v Superman: Dawn of Justice"},
    ...
  ]
}
total is how many movies matched in all, not just the ones on this page. A frontend needs that to show "page 1 of 6".

Hints (try without them first):

Limit rules: use Query(10, ge=1, le=50). ge means "greater than or equal to", and le means "less than or equal to". FastAPI then rejects bad values for you.
Searching: pandas has .str.contains(...) on a text column. Look at its case= setting. Also set regex=False, so a title search like "(500)" doesn't break.
Paging: .iloc[start:end] takes rows from position start up to end. With offset and limit, what are start and end?
Converting to JSON: .to_dict('records') turns rows into a list of dictionaries, which is exactly the shape you need.
Done when
Check each of these in your browser or at /docs:

Visit	Should show
/movies?limit=3	total: 4800, with Avatar, Pirates of the Caribbean: At World's End and Spectre
/movies?search=bat&limit=5	total: 26, starting with "Batman v Superman: Dawn of Justice"
/movies?search=BAT&limit=5	Exactly the same as above (capitals are ignored)
/movies?search=bat&limit=5&offset=5	Page 2: Batman & Robin, Batman Forever, Batman Returns, Battlefield Earth, Battle: Los Angeles
/movies?search=zzzz	total: 0 and results: [], not an error
/movies?limit=100	Error 422 ("less than or equal to 50")
The search matching "Battleship" and "Battle: Los Angeles" isn't a bug. They contain "bat" too.

Last thing: add these two lines to requirements.txt, since the project now uses them:



Step	What you build	What you learn
2	GET /movies/{movie_id}: one movie's details, or a 404 error if the ID doesn't exist	Path parameters, HTTPException
3	GET /movies/{movie_id}/recommendations?k=5: the 5 most similar movies, with the logic moved into its own file, api/recommender.py	Loading similarity.pkl, Pydantic response models, keeping logic separate from routes
4	Posters in the API: get each poster from TMDB, remember it so you don't ask twice, and use a fallback image if there's none	Calling another API from yours, caching, handling missing data
5	Streamlit talks to your API instead of opening the .pkl files	Frontend and backend working together
6	Automatic tests with pytest	Testing endpoints so you know nothing broke

### step3
Visit	Should show
/movies/272/recommendations	Batman Begins: The Dark Knight (0.387), The Dark Knight Rises (0.35), Batman & Robin (0.315), Batman (0.301), Amidst the Devil's Wings (0.295)
/movies/272/recommendations?k=3	Only the first 3 of those
/movies/19995/recommendations?k=3	Avatar: Titan A.E., Independence Day, Small Soldiers
/movies/999999/recommendations	404: "Movie 999999 not found"
/movies/272/recommendations?k=0	422 (must be at least 1)
/movies/272/recommendations?k=21	422 (must be at most 20)
Also open /docs and check that the new endpoint shows the response shape under "Responses". That's your Pydantic model at work.

How the request flows:


/movies/272/recommendations?k=5
  → main.py checks k (1–20)
  → get_movie(272)       404 if it doesn't exist, otherwise Batman Begins
  → recommend(...)       recommender.py: sort the scores, take the top 5
  → Pydantic checks the shape
  → JSON goes back to the user