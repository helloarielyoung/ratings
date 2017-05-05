"""Utility file to seed ratings database from MovieLens data in seed_data/"""

from sqlalchemy import func
from model import User
from model import Rating
from model import Movie

from model import connect_to_db, db
from server import app

from datetime import datetime

def load_users():
    """Load users from u.user into database."""

    print "Users"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    User.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.user"):
        row = row.rstrip()
        user_id, age, gender, occupation, zipcode = row.split("|")

        user = User(user_id=user_id,
                    age=age,
                    zipcode=zipcode)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    #adding our Judgemental Eye
    eye = User(user_id=max_id+1, email='the-eye@of-judgment.com', password='evil')
    db.session.add(eye)
    db.session.commit()


def load_movies():
    """Load movies from u.item into database."""
    print "Movies"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Movie.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.item"):
        row = row.rstrip()
        movie_id, title, released_str, blank, imdb_url = row.split("|")[:5]

        if released_str:
            released_at = datetime.strptime(released_str, "%d-%b-%Y")
        else:
            released_at = None

        movie = Movie(movie_id=movie_id,
                      title=title[:-7],
                      released_at=released_at,
                      imdb_url=imdb_url)

        # We need to add to the session or it won't ever be stored
        db.session.add(movie)

    # Once we're done, we should commit our work
    db.session.commit()


def load_ratings():
    """Load ratings from u.data into database."""
    Rating.query.delete()

    for row in open("seed_data/u.data"):
        row = row.rstrip()
        user_id, movie_id, score, rating_id = row.split("\t")

        rating = Rating(user_id=user_id,
                        movie_id=movie_id,
                        score=score)

        # We need to add to the session or it won't ever be stored
        db.session.add(rating)

    # Once we're done, we should commit our work
    db.session.commit()

    #Add the Judgmental Eye's ratings
    eye = User.query.filter(User.email == 'the-eye@of-judgment.com').one()

    # Toy Story
    r = Rating(user_id=eye.user_id, movie_id=1, score=1)
    db.session.add(r)

    # Robocop 3
    r = Rating(user_id=eye.user_id, movie_id=1274, score=5)
    db.session.add(r)

    # Judge Dredd
    r = Rating(user_id=eye.user_id, movie_id=373, score=5)
    db.session.add(r)

    # 3 Ninjas
    r = Rating(user_id=eye.user_id, movie_id=314, score=5)
    db.session.add(r)

    # Aladdin
    r = Rating(user_id=eye.user_id, movie_id=95, score=1)
    db.session.add(r)

    # The Lion King
    r = Rating(user_id=eye.user_id, movie_id=71, score=1)
    db.session.add(r)

    db.session.commit()

def set_val_user_id():
    """Set value for the next user_id after seeding database"""

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_users()
    load_movies()
    load_ratings()
    set_val_user_id()
