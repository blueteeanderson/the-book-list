"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///the-book-list-test"


from app import app

ctx = app.app_context()
ctx.push()

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 500
        u = User.signup("tee", "tee@test.com", "fuzz", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """test message"""
        
        m = Message(
            text="a warble",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "a warble")

    def test_message_likes(self):
        '''user liked messages'''
        msg = Message(
            text="a warble",
            user_id=self.uid
        )

        u = User.signup("pete", "pete@gmail.com", "fuz", None)
        uid = 501
        u.id = uid
        db.session.add_all([msg, u])
        db.session.commit()

        u.likes.append(msg)

        db.session.commit()

        l = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, msg.id)


        