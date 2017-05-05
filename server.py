"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import jsonify
from flask import (Flask, render_template, redirect, request, flash,
                   session, url_for)
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import update

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/login')
def login():
    """Display login form"""

    return render_template("login_form.html")


@app.route('/login-completion', methods=["POST"])
def authenticate_login():
    """authenticates user info and logs in"""

    email = request.form.get("email")
    password = request.form.get("password")

    if User.query.filter_by(email=email).first() is not None:
        user = User.query.filter_by(email=email).first()
        if user.password == password:
            session['login'] = user.user_id
            print session
            flash('You were successfully logged in')
            user_id = user.user_id
            return redirect('/users/' + str(user_id))
        else:
            flash('Bad password or user name')
            return redirect('/login')
    # we tried getting rid of what appears to be redundant else
    # but it did not work if it was valid email and bad password
    else:
        flash('Bad password or user name')
        return redirect('/login')


@app.route('/logout')
def logout():
    """logs out user"""

    del session['login']
    print session
    flash("You are logged out")

    return redirect('/')


@app.route('/users/<user_id>')
def get_user(user_id):
    """Display user page"""

    user = User.query.get(user_id)

    return render_template('user.html', user=user)


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/register', methods=["GET"])
def give_form():
    """Display form to register new user"""

    return render_template("register_form.html")


@app.route('/register', methods=["POST"])
def register_process():
    """Create new user login from registration form"""

    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    # check if email exists, and if not add to DB
    if User.query.filter_by(email=email).first() is not None:
        flash("You already have an account!")

    else:
        user = User(email=email,
                    password=password,
                    age=age,
                    zipcode=zipcode)
        db.session.add(user)
        db.session.commit()
        flash("You are registered!")

    return redirect("/")


@app.route('/movies')
def movie_list():
    """List of the movies"""

    movies = Movie.query.order_by(Movie.title).all()

    return render_template('movie_list.html', movies=movies)


@app.route('/movie/<movie_id>')
def movie_detail(movie_id):
    """Displays movie details"""

    movie = Movie.query.get(movie_id)

    user_id = session.get('login')

    #Get average rating of movie

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it.

    user_rating = Rating.query.filter_by(
        movie_id=movie_id, user_id=user_id).first()

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    #Judgemental Eye code
    #Either use the prediction or Their real rating
    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None

     # Get the eye's rating, either by predicting or using real rating

    the_eye = (User.query.filter_by(email="the-eye@of-judgement.com")
                         .one())
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    # Depending on how different we are from the Eye, choose a
    # message

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
            "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
            "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    return render_template('movie.html',
                           movie=movie,
                           user_rating=user_rating,
                           average=avg_rating,
                           prediction=prediction,
                           beratement=beratement)


@app.route('/rating-form')
def rating_form():
    """Return ratings form for that movie_id"""

    movie_id = request.args.get("movie_id")
    movie = Movie.query.get(int(movie_id))

    return render_template('rating_form.html', movie=movie)


@app.route('/process-rating', methods=["POST"])
def process_rating():
    """Save rating to ratings table"""
    user_id = session['login']
    movie_id = request.form.get("movie_id")
    score = request.form.get("score")

    rating = db.session.query(Rating).filter_by(user_id=user_id, movie_id=movie_id).first()
    if rating:
        rating.score = score

    else:
        rating = Rating(user_id=user_id,
                        movie_id=movie_id,
                        score=score)

    db.session.add(rating)
    db.session.commit()

    flash("Score recorded")
    return redirect('/')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    app.run(port=5000, host='0.0.0.0')
