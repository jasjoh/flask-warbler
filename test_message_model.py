"""Message model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Follow
from sqlalchemy import exc

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

from app import app

db.drop_all()
db.create_all()

class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()



        u1 = User.signup("u1", "u1@email.com", "password", None)


        db.session.commit()

        self.u1_id = u1.id

        m1 = Message(text="new message", user_id=self.u1_id)


        db.session.add(m1)
        db.session.commit()

        self.m1_id = m1.id


    def tearDown(self):
        db.session.rollback()


    def test_user_model(self):
        m1 = Message.query.get(self.m1_id)

        # User should have no messages & no followers
        self.assertEqual(Message.query.count(), 1)
        self.assertEqual(m1.text, "new message")