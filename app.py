import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm,UserProfileForm, ReviewForm
from models import db, connect_db, User, Review, Like
import requests

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "thr4%jfjLLndneoo*&rt!ffh")
#astoolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash('You have been logged out of your account ccount!', "success")
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = []
    return render_template('users/show.html', user=user, messages=messages)



@app.route('/users/<int:user_id>/likes')
def users_likes(user_id):
    """Show list of likes of this user."""
 
    if not g.user or g.user.id != int(user_id):
        flash("Access unauthorized.", "danger")
        return redirect("/")
    books = []

    likes = (Like
            .query
            .filter(Like.user_id == user_id)
            .all())
    
    for like in likes:
        resp = requests.get(
            f"https://openlibrary.org/works/{like.book_key}.json",
            params={}
        )
        resp = resp.json()

        # make sure there is a description
        desc = resp.get("description", 'No description')
    
        if isinstance(desc, dict):
            desc = desc.get("value",'No description')

        # make sure there is a cover
        cover = resp.get("covers", ['No image available'])
        cover = cover[0]

        # make sure there is a published date
        published = resp.get("first_publish_date", 'No date available')

        authors = []

        for author in resp['authors']:
            authorResp = requests.get(
                f"https://openlibrary.org/{author['author']['key']}.json",
                params={}
            )

            authorResp = authorResp.json()

            authors.append(authorResp['name'])
            authors = list(set(authors ))
        

        book = {
            "title": resp['title'],
            "published": published,
            "description": desc,
            "authors" : authors,
            "cover" : cover,
            "key" : like.book_key
        }

        books.append(book)


    return render_template("/users/likes.html", books=books)

@app.route('/users/<int:user_id>/<key>', methods=["GET"])
def users_book_details(user_id,key):
    """ Show a book's details"""
    
    if not g.user or g.user.id != int(user_id):
        flash("Access unauthorized.", "danger")
        return redirect("/")

    resp = requests.get(
            f"https://openlibrary.org/works/{key}.json",
            params={}
       )
       
    resp = resp.json()

    # make sure there is a description
    desc = resp.get("description", 'No description')
  
    if isinstance(desc, dict):
        desc = desc.get("value",'No description')

    # make sure there is a cover
    cover = resp.get("covers", ['No image available'])
    cover = cover[0]

    # make sure there is a published date
    published = resp.get("first_publish_date", 'No date available')

    authors = []

    for author in resp['authors']:
        authorResp = requests.get(
            f"https://openlibrary.org/{author['author']['key']}.json",
            params={}
        )

        authorResp = authorResp.json()

        authors.append(authorResp['name'])
        authors = list(set(authors ))

    # get reviews and user associated with book
    reviews = (Review
            .query
            .filter(Review.book_key == key)
            .order_by(Review.timestamp.desc())
            .limit(100)
            .all())
    

    book = {
        "title": resp['title'],
        "published": published,
        "description": desc,
        "authors" : authors,
        "cover" : cover,
        "key" : key,
        "reviews" : reviews,
        "user_id" : user_id
    }

    return render_template('users/book.html', book=book)

@app.route('/users/<int:user_id>/<book_key>/review', methods=["GET", "POST"])
def user_review_add(user_id,book_key):
    """Add a review:

    Show form if GET. If valid, update review and redirect to book page.
    """

    if not g.user or g.user.id != int(user_id):
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = ReviewForm()

    if form.validate_on_submit():
        review = Review(review=form.review.data,book_key=book_key,user_id=g.user.id)
        db.session.add(review)
        db.session.commit()

        return redirect(f"/users/{user_id}/{book_key}")

    return render_template('users/review.html', form=form)

"""
@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
   

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/add_like/<int:message_id>', methods=['POST'])
def add_like(message_id):
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    #get message includes user id
    msg = Message.query.get_or_404(message_id)
    #if the message is by user, fobid access to liking it
    if msg.user_id == g.user.id:
        return abort(403)
    #remove like 
    if msg in g.user.likes:
        g.user.likes = [like for like in g.user.likes if like != msg]
    #add like
    else:
        g.user.likes.append(msg)
    db.session.commit()

    return redirect("/")
"""

@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    #if invalid user
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")


    form = UserProfileForm(obj= g.user)


    if form.validate_on_submit():
        #check to see if valid user
        password_to_check = form.password.data
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            g.user.first_name = form.first_name.data
            g.user.last_name = form.last_name.data
            g.user.username = form.username.data
            g.user.email = form.email.data
            db.session.commit()

            return redirect(f"/users/{g.user.id}")
        else:
            flash("Invalid credentials.", 'danger')

 
    return render_template("/users/edit.html", form=form)
    

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:
"""
@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):


    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")
"""

##############################################################################
# books pages

@app.route('/books/trending', methods=["GET"])
def books_trending():
    """ Show a list of trending books"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    resp = requests.get(
            "https://openlibrary.org/trending/now.json?limit=15",
            params={}
       )
       
    books = resp.json()['works']
    for book in books:
        book['author_name'] = book.get("author_name", ["No author listed"]) #default if no author
        book['author_name'] = list(set(book['author_name'] )) #remove dupes
        book['key'] = book['key'].replace("works/","")
        book['key'] = "/books/book/" + book['key']

    return render_template('books/index.html', books=books)

@app.route('/books/book/<key>', methods=["GET"])
def book_details(key):
    """ Show a book's details"""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    resp = requests.get(
            f"https://openlibrary.org/works/{key}.json",
            params={}
       )
       
    resp = resp.json()

    # make sure there is a description
    desc = resp.get("description", 'No description')
  
    if isinstance(desc, dict):
        desc = desc.get("value",'No description')

    # make sure there is a cover
    cover = resp.get("covers", ['No image available'])
    cover = cover[0]

    # make sure there is a published date
    published = resp.get("first_publish_date", 'No date available')

    authors = []

    for author in resp['authors']:
        authorResp = requests.get(
            f"https://openlibrary.org/{author['author']['key']}.json",
            params={}
        )

        authorResp = authorResp.json()

        authors.append(authorResp['name'])
        authors = list(set(authors ))

    # get reviews and user associated with book
    reviews = (Review
            .query
            .filter(Review.book_key == key)
            .order_by(Review.timestamp.desc())
            .limit(100)
            .all())
    

    book = {
        "title": resp['title'],
        "published": published,
        "description": desc,
        "authors" : authors,
        "cover" : cover,
        "key" : key,
        "reviews" : reviews
    }

    return render_template('books/book.html', book=book)

@app.route('/books/book/<book_key>/review', methods=["GET", "POST"])
def review_add(book_key):
    """Add a review:

    Show form if GET. If valid, update review and redirect to book page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = ReviewForm()

    if form.validate_on_submit():
        review = Review(review=form.review.data,book_key=book_key,user_id=g.user.id)
        db.session.add(review)
        db.session.commit()

        return redirect(f"/books/book/{book_key}")

    return render_template('books/review.html', form=form)


##############################################################################
# likes pages
@app.route('/books/book/<book_key>/like', methods=[ "POST"])
def like_add(book_key):
    """ Add a like  """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")


    
    like = Like(book_key=book_key,user_id=g.user.id)
    db.session.add(like)
    db.session.commit()

    flash("Book has been added to your likes.", "success")
    return redirect(f"/books/book/{book_key}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        #session.query(Customers).filter(or_(Customers.id>2, Customers.name.like('Ra%')))

        messages = []

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
