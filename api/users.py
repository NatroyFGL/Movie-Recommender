from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Field, Session, SQLModel, select

from api.database import Movie, Rating, User, get_session

router = APIRouter(prefix='/users', tags=['users'])

#shapes of the request bodies
class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=30)

class RatingIn(SQLModel):
    stars: int = Field(ge=1, le=5)

#find one user by id, or stop with 404
def find_user(session, user_id):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f'User {user_id} not found')
    return user

#CREATE a user
@router.post('', status_code=201)
def create_user(new_user: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.username == new_user.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f'Username {new_user.username} is taken')

    user = User.model_validate(new_user)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

#READ one user
@router.get('/{user_id}')
def get_user(user_id: int, session: Session = Depends(get_session)):
    return find_user(session, user_id)

#rate a movie: creates the rating the first time, changes it after that
@router.put('/{user_id}/ratings/{movie_id}')
def rate_movie(user_id: int, movie_id: int, body: RatingIn, session: Session = Depends(get_session)):
    find_user(session, user_id)
    movie = session.exec(select(Movie).where(Movie.movie_id == movie_id)).first()
    if movie is None:
        raise HTTPException(status_code=404, detail=f'Movie {movie_id} not found')

    rating = session.exec(
        select(Rating).where(Rating.user_id == user_id, Rating.movie_id == movie_id)
    ).first()
    if rating is None:
        rating = Rating(user_id=user_id, movie_id=movie_id, stars=body.stars)
    else:
        rating.stars = body.stars

    session.add(rating)
    session.commit()
    session.refresh(rating)
    return {'user_id': user_id, 'movie_id': movie_id, 'title': movie.title, 'stars': rating.stars}

#all ratings of one user, with the movie titles (JOIN rating + movie tables)
@router.get('/{user_id}/ratings')
def list_ratings(user_id: int, session: Session = Depends(get_session)):
    find_user(session, user_id)
    rows = session.exec(
        select(Rating, Movie)
        .join(Movie, Rating.movie_id == Movie.movie_id)
        .where(Rating.user_id == user_id)
        .order_by(Rating.id)
    ).all()
    return [{'movie_id': movie.movie_id, 'title': movie.title, 'stars': rating.stars} for rating, movie in rows]
