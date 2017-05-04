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

    movies = Movie.query.all()

    return render_template('movie_list.html', movies=movies)


@app.route('/movie/<movie_id>')
def movie_detail(movie_id):
    """Displays movie details"""

    movie = Movie.query.get(movie_id)

    return render_template('movie.html', movie=movie)


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
