"""SQLAlchemy models for The Book List."""

from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()




class Like(db.Model):
    """Mapping user likes to warbles."""

    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    book_key = db.Column(
        db.Text,
    )

    user = db.relationship('User')

class Review(db.Model):
    """Mapping user reviews to books."""

    __tablename__ = 'reviews' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        nullable=False,
    )

    book_key = db.Column(
        db.Text,
        nullable=False
    )

    review = db.Column(
        db.Text,
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    user = db.relationship('User')

class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    first_name = db.Column(
        db.Text,
        nullable=False,
    )

    last_name = db.Column(
        db.Text,
        nullable=False,
    )



    """ !delete
    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )
    
    
    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )
    

    bio = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )
    """
    

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"


    @classmethod
    def signup(cls, username, first_name, last_name, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
