"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_is_following(self):
        """Test to see if is_following works.
        Testing if u1 is following u2, but also if u2 is not following u1"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u2.followers.append(u1) #  u1.folowing.append(u2) same statements

        #TODO: do we need to commit?

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

    def test_is_followed_by(self):
        """Test to see if is_followed_by works.
        Testing if u2 is being followed by u1,
        but also u1 is not being followed by u2"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u2.followers.append(u1)

        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))



    def test_signup(self):
        """Tests that a new user can be successfully created, with valid
        credentials, and fail if not valid """

        User.signup(
            username='newuser',
            email='newuser@gmail.com',
            password='newuserpassword',
            image_url='',
            )

        self.assertEqual(User.query.count(), 3)

    def test_signup_not_null(self):
        """Test to see that a null username (None), raises an error."""

        #TODO: why cant we say app.IntegrityError
        with self.assertRaises(exc.IntegrityError) as cm:
            User.signup(
                username=None,
                email='newuser1@gmail.com',
                password='newuserpassword',
                image_url='',
            )
            db.session.flush()

        self.assertIn("NotNullViolation", str(cm.exception))


    def test_signup_not_unique(self):
        """Tests to see that username uniqueness raises an error, the username
        is already being used."""

        User.signup(
            username='newuser',
            email='newuser@gmail.com',
            password='newuserpassword',
            image_url='',
            )

        with self.assertRaises(exc.IntegrityError) as cm:
            User.signup(
                username='newuser',
                email='newuser1@gmail.com',
                password='newuserpassword',
                image_url='',
            )

            db.session.flush()
        self.assertIn("UniqueViolation", str(cm.exception))


    def test_authenticate_success(self):
        """Tests that we successfully return a user when given a valid username
        and password"""

        u1 = User.authenticate(username="u1",  password="password")

        # self.assertTrue(type(u1) == User)
        self.assertTrue(u1)

    def test_authenticate_username_fail(self):
        """Tests that authentication returns false when the wrong username
        is provided"""
        u1 = User.authenticate(username="foobar",  password="password")

        self.assertFalse(u1)

    def test_authenticate_password_fail(self):
        """Tests that authentication returns false when the wrong username
        is provided"""

        u1 = User.authenticate(username="u1",  password="bob")

        self.assertFalse(u1)