"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db
from models import User, Review, Likes
from app import app

app.app_context().push()
db.drop_all()
db.create_all()

