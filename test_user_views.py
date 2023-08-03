"""User view function tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follow
from sqlalchemy import exc

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app

app.config['TESTING'] = True

db.drop_all()
db.create_all()

# TODO: Why can't we get this via app.CURR_USER_KEY?
CURR_USER_KEY = "curr_user"


class UserViewsTestCase(TestCase):
    """Tests for views associated with users."""

    def setUp(self):
        """Make demo data."""

        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u1_username = u1.username
        self.u2_id = u2.id


    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    # def login_u1(self):
    #     """ Logs in user 1 and returns """
    #     with app.test_client() as client:
    #         with client.session_transaction() as change_session:
    #             change_session[CURR_USER_KEY] = self.u1_id

    # def logout_u1(self):
    #     """ Logs in user 1 and returns """
    #     with app.test_client() as client:
    #         with client.session_transaction() as change_session:
    #             del change_session[CURR_USER_KEY]

    def test_list_users_logged_in(self):
        """ Tests to make sure users endpoint shows a list of users """
        with app.test_client() as client:
            # set user 1 as logged in
            with client.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.u1_id

            resp = client.get("/users")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("users-index-test", html)

    def test_list_users_logged_out(self):
        """ Tests to make sure /users endpoint redirects to root
        when not logged in """

        with app.test_client() as client:

            resp = client.get("/users")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

    def test_list_users_search(self):
        """ Tests to make sure users endpoint supports searching for u1,
         shows u1 on the page and does NOT show u2 """
        with app.test_client() as client:
            # set user 1 as logged in
            with client.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.u1_id

            resp = client.get("/users?q=u1")

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("users-index-test", html)
            self.assertIn("u1", html)
            self.assertNotIn("u2", html)

    def test_user_page_valid_logged_in(self):
        """ Test user page while logged into to ensure we get right page """
        with app.test_client() as client:
            # set user 1 as logged in
            with client.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.u1_id

        resp = client.get(f"/users/{self.u1_id}")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("users-show-test", html)


    # Other Tests
    # Un-follow correctly shows as un-followed
    # Delete user correctly deletes a user and doesn't break DB