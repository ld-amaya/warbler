"""Message Model Test Case"""

from app import app
import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


db.create_all()


class MessageModelTest(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test data"""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup('user1', "user1@user1.com", "123456", None)
        user2 = User.signup('user2', "user2@user2.com", "123456", None)

        db.session.commit()

        self.user1 = user1
        self.user2 = user2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    # Does basic model work

    def test_message_model(self):
        message1 = Message(text="This is first message", user_id=self.user1.id)
        message2 = Message(text="Hello Lou", user_id=self.user1.id)
        message3 = Message(text="Hello user2", user_id=self.user2.id)

        db.session.add(message1)
        db.session.add(message2)
        db.session.add(message3)
        db.session.commit()

        user1 = User.query.get(self.user1.id)
        user2 = User.query.get(self.user2.id)
        self.assertEqual(len(user1.messages), 2)
        self.assertEqual(len(user2.messages), 1)
        self.assertEqual(user1.messages[1].text, "Hello Lou")
        self.assertEqual(user2.messages[0].text, "Hello user2")

    # Does follower can like message
    def test_message_like(self):
        message1 = Message(text="Hello lou", user_id=self.user1.id)
        message2 = Message(text="Hello to you too", user_id=self.user1.id)
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()

        user1 = User.query.get(self.user1.id)
        user2 = User.query.get(self.user2.id)

        user1.likes.append(message1)
        user1.likes.append(message2)

        db.session.commit()

        self.assertEqual(len(user1.likes), 2)
        self.assertEqual(len(user2.likes), 0)
