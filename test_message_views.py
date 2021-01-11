"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase
from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        # add messages
        message1 = Message(text="This is first message",
                           user_id=self.testuser.id)

        db.session.add(message1)
        db.session.commit()

        self.message = message1

    def test_add_message(self):
        """Can authenticate user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new",
                          data={"text": "Hello"},
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello", html)

    def test_add_message_unauthenticated(self):
        """Can unauthenticated user can add a message"""

        with self.client as client:
            response = client.post("/messages/new",
                                   data={'text': 'hello'},
                                   follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_show_message(self):
        """Can view message"""

        with self.client as client:

            response = client.get(f'/messages/{self.message.id}')
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("This is first message", html)

    def test_delete_message(self):
        """Can authorized user delete a message"""
        with app.test_client() as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="This message is to be deleted",
                          user_id=self.testuser.id)

            db.session.add(msg)
            db.session.commit()

            # Check if message is added
            res = client.get(f'/messages/{msg.id}')
            data_html = res.get_data(as_text=True)
            self.assertIn("This message is to be deleted", data_html)

            response = client.post(
                f'/messages/{msg.id}/delete', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Message deleted", html)

    def test_delete_message_unauthorized(self):
        """Can unauthorized user delete a message"""

        with app.test_client() as client:
            response = client.post(
                f'/messages/{self.message.id}/delete', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", html)
