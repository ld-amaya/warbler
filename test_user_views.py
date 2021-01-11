"""User view tests"""

import os
from app import app, CURR_USER_KEY
from unittest import TestCase
from models import db, connect_db, User, Follows, Likes, Message
from bs4 import BeautifulSoup


os.environ['DATABASE_URI'] = "postgresql:///warbler-test"
app.config['SQLALCHEMY_ECHO'] = False

db.create_all()


class UserViewTest(TestCase):
    """Test user views"""

    def setUp(self):
        """Create seed data to be added to the user model"""

        # Disable wtf csrf token validation
        app.config['WTF_CSRF_ENABLED'] = False

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()
        Follows.query.delete()

        # add users
        user1 = User.signup('user1', 'user1@user1.com', '123456', None)
        user2 = User.signup('user2', 'user2@user1.com', '654321', None)
        user3 = User.signup('user3', 'user3@user3.com', 'abcdef', None)

        db.session.commit()
        self.user1 = user1
        self.user2 = user2
        self.user3 = user3

        # add messages
        message1 = Message(text="This is first message", user_id=self.user1.id)
        message2 = Message(text="Hello Lou", user_id=self.user1.id)
        message3 = Message(text="Hello user2", user_id=self.user1.id)

        db.session.add_all([message1, message2, message3])
        db.session.commit()

        # add following
        self.user1.following.append(self.user2)
        self.user1.following.append(self.user3)
        db.session.commit()

        # add followers
        self.user1.followers.append(self.user3)
        db.session.commit()

    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response

    def test_user_signup(self):
        """test new user signup"""
        with app.test_client() as client:
            data = {
                'username': 'lou',
                'email': 'lou@lou.com',
                'password': 'password',
                'image_url': 'https://images.unsplash.com/photo-1541832186590-2bffabbc08db?ixid=MXwxMjA3fDB8MHxzZWFyY2h8MTV8fGhlYWRzaG90fGVufDB8fDB8&ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60'
            }
            response = client.post('/signup', data=data, follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<p>@lou</p>', html)

    def test_user_login(self):
        """test user login"""
        with app.test_client() as client:
            response = client.post(
                '/login',
                data={'username': 'user1',
                      'password': '123456'},
                follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('<p>@user1</p>', html)

    def test_users(self):
        """test user list"""

        with app.test_client() as client:
            response = client.get("/users")
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('@user1', html)
            self.assertIn('@user2', html)

    def test_user_profile(self):
        """testing get request profile view"""
        with app.test_client() as client:
            response = client.get(f'/users/{self.user1.id}')
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)

            mySoup = BeautifulSoup(str(response.data), 'html.parser')
            found = mySoup.find_all('li', {'class': 'stat'})

            self.assertEqual(len(found), 4)
            # Test number of messages
            self.assertIn('3', found[0].text)
            # Test number of followings
            self.assertIn('2', found[1].text)
            # Test number of followers
            self.assertIn('1', found[2].text)
            # Test number of likes
            self.assertIn('0', found[3].text)
            # Test user message
            self.assertIn('This is first message', html)
            self.assertIn('Hello Lou', html)
            self.assertIn('Hello user2', html)

    def test_view_user_following_authenticated(self):
        """test authenticated user to show user following"""
        with app.test_client() as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get(f'/users/{self.user1.id}/following')
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('user2', html)
            self.assertIn('user3', html)

    def test_view_user_following_unauthenticated(self):
        """test unauthenticated user in accessing user following"""
        with app.test_client() as client:
            response = client.get(
                f'/users/{self.user1.id}/following', follow_redirects=True)
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_view_user_follower_authenticated(self):
        """test authenticated user to show user followers"""
        with app.test_client() as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.get(f'/users/{self.user1.id}/followers')
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('user3', html)

    def test_view_user_followers_unauthorized(self):
        """test unauthenticated user in accessing user followers"""
        with app.test_client() as client:
            response = client.get(
                f'/users/{self.user1.id}/followers', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn('Access unauthorized.', html)

    def test_follow_user_authenticated(self):
        """test authenticated user following new user"""

        with app.test_client() as client:

            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.user1.id

            response = client.post(
                f'/users/follow/{self.user1.id}', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)

            mySoup = BeautifulSoup(str(response.data), 'html.parser')
            found = mySoup.find_all('li', {'class': 'stat'})

            self.assertIn('3', found[1].text)

    def test_follow_user_unauthenticated(self):
        """test unauthenticated user following new uesr"""
        with app.test_client() as client:
            response = client.post(
                f'/users/follow/{self.user1.id}', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_unfollow_user_authenticated(self):
        """test authenticated user unfollowing currently followed user"""
        with app.test_client() as client:

            login = User.authenticate(self.user1.username, self.user1.password)

            if login:
                session[CURR_USER_KEY] = login.id
                response = client.post(
                    f"/users/stop-following/{self.user2.id}", follow_redirects=True)
                html = response.get_data(as_text=True)

                self.assertEqual(response.status_code, 200)

                mySoup = BeautifulSoup(str(response.data), 'html.parser')
                found = mySoup.find_all('li', {'class': 'stat'})

                self.assertIn('1', found[1].text)

    def test_unfollow_user_unauthenticated(self):
        """test unauthenticated user unfollowing user"""
        with app.test_client() as client:
            response = client.post(
                f'/users/stop-following/{self.user1.id}', follow_redirects=True)
            html = response.get_data(as_text=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)
