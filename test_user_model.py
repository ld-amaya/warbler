"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User.signup('user1', "user1@user1.com", "123456", None)
        user2 = User.signup('user2', "user2@user2.com", "123456", None)

        db.session.commit()

        self.user1 = user1
        self.user2 = user2

        self.user_id1 = user1.id
        self.user_id2 = user2.id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    # Does is_following successfully detect when user1 is following user2?
    def test_is_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user1.followers), 0)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    # Does is_following successfully detect when user1 is not following user2?
    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    # Does is_followed_by successfully detect when user1 is followed by user2?
    # Does is_followed_by successfully detect when user1 is not followed by user2?
    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    # Does User.create successfully create a new user given valid credentials?
    def test_user_create(self):
        user3 = User.signup('user3', 'user3@user3.com', 'pass123', None)
        uid = 9999
        user3.id = uid
        db.session.commit()

        new_user = User.query.get(uid)
        self.assertEqual(new_user.username, 'user3')
        self.assertEqual(new_user.email, 'user3@user3.com')
        self.assertNotEqual(new_user.password, 'pass123')

    # Does User.create fail to create a new user if any of the validations(e.g. uniqueness, non-nullable fields) fail?
    def test_invalid_username(self):
        user4 = User.signup(None, 'user4@user4.com', 'password', None)
        uid = 123456
        user4.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email(self):
        user4 = User.signup('user4', None, 'password', None)
        uid = 123456
        user4.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            user4 = User.signup('user4', 'user4@user4.com', '', None)

    # Does User.authenticate successfully return a user when given a valid username and password?
    def test_user_login(self):
        user = User.authenticate(self.user1.username, "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1.id)

    # Does User.authenticate fail to return a user when the username is invalid?
    def test_user_invalid_username(self):
        self.assertFalse(User.authenticate("notauser", "123456"))

    # Does User.authenticate fail to return a user when the password is invalid?
    def test_user_invalid_password(self):
        self.assertFalse(User.authenticate("self.user1.username", "1234567"))
