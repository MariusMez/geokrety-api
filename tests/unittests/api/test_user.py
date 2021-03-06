from app import current_app as app
from app.api.helpers.db import safe_query
from app.models import db
from app.models.news import News
from app.models.news_comment import NewsComment
from app.models.user import User
from mixer.backend.flask import mixer
from tests.unittests.utils import GeokretyTestCase


class TestUser(GeokretyTestCase):
    """Test User CRUD operations"""

    def _blend(self):
        """Create mocked User/News/NewsComments"""
        mixer.init_app(app)
        with mixer.ctx(commit=False):
            self.admin = mixer.blend(User)
            self.user1 = mixer.blend(User)
            self.user2 = mixer.blend(User)
            self.news1 = mixer.blend(News, author=self.user1)
            self.orphan_news = mixer.blend(News, author=None)
            self.newscomment1 = mixer.blend(NewsComment, author=self.user1, news=self.news1)
            db.session.add(self.admin)
            db.session.add(self.user1)
            db.session.add(self.user2)
            db.session.add(self.news1)
            db.session.add(self.orphan_news)
            db.session.add(self.newscomment1)
            db.session.commit()

    def _check_user_with_private(self, data, user, skip_check=None):
        skip_check = skip_check or []
        attributes = data['data']['attributes']

        self.assertTrue('email' in attributes)
        self.assertTrue('hour' in attributes)
        self.assertTrue('latitude' in attributes)
        self.assertTrue('longitude' in attributes)
        self.assertTrue('observation-radius' in attributes)
        self.assertTrue('secid' in attributes)
        self.assertTrue('statpic-id' in attributes)
        self.assertTrue('last-login-date-time' in attributes)
        self.assertTrue('last-mail-date-time' in attributes)
        self.assertTrue('last-update-date-time' in attributes)

        self.assertEqual(attributes['email'], user.email)
        self.assertTrue(isinstance(attributes['hour'], int))
        self.assertEqual(attributes['latitude'], user.latitude)
        self.assertEqual(attributes['longitude'], user.longitude)
        self.assertEqual(attributes['observation-radius'], user.observation_radius)
        self.assertEqual(attributes['secid'], user.secid)
        self.assertEqual(attributes['statpic-id'], user.statpic_id)

        if 'times' not in skip_check:
            if attributes['last-login-date-time']:
                self.assertDateTimeEqual(attributes['last-login-date-time'], user.last_login_date_time)
            if attributes['last-mail-date-time']:
                self.assertDateTimeEqual(attributes['last-mail-date-time'], user.last_mail_date_time)
            if attributes['last-update-date-time']:
                self.assertDateTimeEqual(attributes['last-update-date-time'], user.last_update_date_time)

    def _check_user_without_private(self, data, user, skip_check=None):
        skip_check = skip_check or []
        self.assertTrue('attributes' in data['data'])
        self.assertTrue('name' in data['data']['attributes'])
        attributes = data['data']['attributes']

        self.assertTrue('name' in attributes)
        self.assertTrue('country' in attributes)
        self.assertTrue('language' in attributes)
        self.assertTrue('join-date-time' in attributes)

        self.assertFalse('password' in attributes)
        self.assertFalse('ip' in attributes)
        self.assertFalse('statpic-id' in attributes)
        self.assertFalse('hour' in attributes)
        self.assertFalse('email' in attributes)
        self.assertFalse('latitude' in attributes)
        self.assertFalse('longitude' in attributes)
        self.assertFalse('last-login-date-time' in attributes)
        self.assertFalse('last-mail-date-time' in attributes)
        self.assertFalse('last-update-date-time' in attributes)

        self.assertEqual(attributes['name'], user.name)
        self.assertEqual(attributes['country'], user.country)
        self.assertEqual(attributes['language'], user.language)

        if 'times' not in skip_check:
            self.assertDateTimeEqual(attributes['join-date-time'], user.join_date_time)

    def test_post_content_types(self):
        """Check User: POST accepted content types"""
        self._send_post("/v1/users", payload="not a json", code=415, content_type='application/json')
        self._send_post("/v1/users", payload={}, code=422)
        self._send_post("/v1/users", payload={"user": "kumy"}, code=422)

    def test_create_incomplete(self):
        """Check User: POST incomplete request"""
        payload = {
            "data": {
                "type": "user"
            }
        }
        self._send_post("/v1/users", payload=payload, code=422)

    def test_create_without_username(self):
        """Check User: POST request without username"""
        with app.test_request_context():
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                            "password": someone.password,
                            "email": someone.email
                    }
                }
            }
            self._send_post("/v1/users", payload=payload, code=422)

    def test_create_without_password(self):
        """Check User: POST without password"""
        with app.test_request_context():
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                            "name": someone.name,
                            "email": someone.email
                    }
                }
            }
            self._send_post("/v1/users", payload=payload, code=422)

    def test_create_without_email(self):
        """Check User: POST without email"""
        with app.test_request_context():
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                            "name": someone.name,
                            "password": someone.password
                    }
                }
            }
            self._send_post("/v1/users", payload=payload, code=422)

    def test_create_minimal(self):
        """Check User: POST request minimal informations"""
        with app.test_request_context():
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                            "name": someone.name,
                            "password": someone.password,
                            "email": someone.email
                    }
                }
            }
            response = self._send_post("/v1/users", payload=payload, code=201)
            self._check_user_with_private(response, someone, skip_check=['times'])

            users = User.query.all()
            self.assertEqual(len(users), 1)
            user = users[0]
            self.assertEqual(someone.name, user.name)
            self._check_user_with_private(response, user)

    def test_create_complete(self):
        """Check User: POST request full informations"""
        with app.test_request_context():
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                            "name": someone.name,
                            "password": someone.password,
                            "email": someone.email,
                            "hour": someone.hour,
                            "latitude": someone.latitude,
                            "longitude": someone.longitude,
                            "observation-radius": someone.observation_radius,
                            "secid": someone.secid,
                            "statpic-id": someone.statpic_id
                    }
                }
            }
            response = self._send_post("/v1/users", payload=payload, code=201)
            self._check_user_with_private(response, someone, skip_check=['times'])

            users = User.query.all()
            self.assertEqual(len(users), 1)
            user = users[0]
            self.assertEqual(someone.name, user.name)
            self._check_user_with_private(response, user)

    def test_create_user(self):
        """Check User: POST and Read back an user"""
        with app.test_request_context():
            mixer.init_app(app)
            admin = mixer.blend(User)
            someone = mixer.blend(User)
            with mixer.ctx(commit=False):
                user1 = mixer.blend(User)

            # Test inserting first user
            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                        "name": user1.name,
                        "password": user1.password,
                        "email": user1.email
                    }
                }
            }
            response = self._send_post('/v1/users', payload=payload, code=201)
            self._check_user_with_private(response, user1, skip_check=['times'])
            user1.id = response['data']['id']

            response = self._send_get('/v1/users/%s' % user1.id, code=200)
            self._check_user_without_private(response, user1, skip_check=['times'])

            response = self._send_get('/v1/users/%s' % user1.id, code=200, user=user1)
            self._check_user_with_private(response, user1, skip_check=['times'])

            response = self._send_get('/v1/users/%s' % user1.id, code=200, user=admin)
            self._check_user_with_private(response, user1, skip_check=['times'])

            response = self._send_get('/v1/users/%s' % user1.id, code=200, user=someone)
            self._check_user_without_private(response, user1, skip_check=['times'])

    def test_create_user_name_uniqueness(self):
        """Check User: POST name uniqueness"""
        with app.test_request_context():
            self._blend()
            with mixer.ctx(commit=False):
                user1 = mixer.blend(User)

            # Test inserting first user
            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                        "name": self.user1.name,
                        "password": user1.password,
                        "email": user1.email
                    }
                }
            }
            self._send_post('/v1/users', payload=payload, code=422)

    def test_create_user_email_uniqueness(self):
        """Check User: POST email uniqueness"""
        with app.test_request_context():
            self._blend()
            with mixer.ctx(commit=False):
                user1 = mixer.blend(User)

            # Test inserting first user
            payload = {
                "data": {
                    "type": "user",
                    "attributes": {
                        "name": user1.name,
                        "password": user1.password,
                        "email": self.user1.email
                    }
                }
            }
            self._send_post('/v1/users', payload=payload, code=422)

    def test_get_user_list(self):
        """Check User: GET user listing must be authenticated"""
        with app.test_request_context():
            self._blend()
            self._send_get('/v1/users', code=401)
            self._send_get('/v1/users', code=200, user=self.admin)
            self._send_get('/v1/users', code=200, user=self.user1)
            self._send_get('/v1/users', code=200, user=self.user2)

    def test_get_user_details(self):
        """Check User: GET user details"""
        with app.test_request_context():
            self._blend()
            url = '/v1/users/%d' % self.user1.id

            response = self._send_get(url, code=200)
            self._check_user_without_private(response, self.user1)

            response = self._send_get(url, code=200, user=self.admin)
            self._check_user_with_private(response, self.user1)

            response = self._send_get(url, code=200, user=self.user1)
            self._check_user_with_private(response, self.user1)

            response = self._send_get(url, code=200, user=self.user2)
            self._check_user_without_private(response, self.user1)

    def test_get_news_author(self):
        """Check User: GET author details from a news"""
        with app.test_request_context():
            self._blend()
            url = '/v1/news/%d/author' % self.news1.id

            response = self._send_get(url, code=200)
            self._check_user_without_private(response, self.user1)
            response = self._send_get(url, code=200, user=self.admin)
            self._check_user_with_private(response, self.user1)
            response = self._send_get(url, code=200, user=self.user1)
            self._check_user_with_private(response, self.user1)
            response = self._send_get(url, code=200, user=self.user2)
            self._check_user_without_private(response, self.user1)

    def test_get_unexistent_news_author(self):
        """Check User: GET author details from an unexistent news"""
        with app.test_request_context():
            self._blend()

            self._send_get('/v1/news/666/author', code=404, user=self.admin)
            self._send_get('/v1/news/666/author', code=404, user=self.user1)
            self._send_get('/v1/news/666/author', code=404, user=self.user2)

    def test_get_news_orphan(self):
        """Check User: GET author details from an orphan news"""
        with app.test_request_context():
            self._blend()
            orphan_url = '/v1/news/%d/author' % self.orphan_news.id

            self._send_get(orphan_url, code=404, user=self.admin)
            self._send_get(orphan_url, code=404, user=self.user1)
            self._send_get(orphan_url, code=404, user=self.user2)

    def test_get_news_comment_author(self):
        """Check User: GET author from a news_comment"""
        with app.test_request_context():
            self._blend()
            response = self._send_get('/v1/news-comments/1/author', code=200, user=self.admin)
            self._check_user_with_private(response, self.user1)
            response = self._send_get('/v1/news-comments/1/author', code=200, user=self.user1)
            self._check_user_with_private(response, self.user1)
            response = self._send_get('/v1/news-comments/1/author', code=200, user=self.user2)
            self._check_user_without_private(response, self.user1)

            self._send_get('/v1/news-comments/666/author', code=404, user=self.admin)
            self._send_get('/v1/news-comments/666/author', code=404, user=self.user1)
            self._send_get('/v1/news-comments/666/author', code=404, user=self.user2)

    def test_patch_list(self):
        """
        Check User: PATCH list cannot be patched
        """
        with app.test_request_context():
            self._blend()
            self._send_patch("/v1/users", code=405)
            self._send_patch("/v1/users", code=405, user=self.admin)
            self._send_patch("/v1/users", code=405, user=self.user1)
            self._send_patch("/v1/users", code=405, user=self.user2)

    def test_patch_anonymous(self):
        """
        Check User: PATCH anonymously is forbidden
        """
        with app.test_request_context():
            self._blend()
            self._send_patch("/v1/users", code=405)
            self._send_patch("/v1/users/1", code=401)
            self._send_patch("/v1/users/2", code=401)
            self._send_patch("/v1/users/3", code=401)
            self._send_patch("/v1/users/4", code=401)

    def test_patch_full_admin_someone(self):
        """
        Check User: PATCH admin can update everyone - Admin
        """
        with app.test_request_context():
            self._blend()
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "id": None,
                    "attributes": {
                            "name": None,
                            "password": someone.password,
                            "email": None,
                            "hour": someone.hour,
                            "latitude": someone.latitude,
                            "longitude": someone.longitude,
                            "observation-radius": someone.observation_radius,
                            "secid": someone.secid,
                            "statpic-id": someone.statpic_id,
                    }
                }
            }

            payload["data"]["id"] = "1"
            payload["data"]["attributes"]["name"] = someone.name = "someone_1"
            payload["data"]["attributes"]["email"] = someone.email = "someone_1@email.email"
            response = self._send_patch("/v1/users/1", payload=payload, code=200, user=self.admin)
            self._check_user_with_private(response, someone, skip_check=['times'])

            payload["data"]["id"] = "2"
            payload["data"]["attributes"]["name"] = someone.name = "someone_2"
            payload["data"]["attributes"]["email"] = someone.email = "someone_2@email.email"
            response = self._send_patch("/v1/users/2", payload=payload, code=200, user=self.admin)
            self._check_user_with_private(response, someone, skip_check=['times'])

            payload["data"]["id"] = "3"
            payload["data"]["attributes"]["name"] = someone.name = "someone_3"
            payload["data"]["attributes"]["email"] = someone.email = "someone_3@email.email"
            response = self._send_patch("/v1/users/3", payload=payload, code=200, user=self.admin)
            self._check_user_with_private(response, someone, skip_check=['times'])

            payload["data"]["id"] = "4"
            payload["data"]["attributes"]["name"] = someone.name = "someone_4"
            payload["data"]["attributes"]["email"] = someone.email = "someone_4@email.email"
            self._send_patch("/v1/users/4", payload=payload, code=404, user=self.admin)

    def test_patch_full_user1_someone(self):
        """
        Check User: PATCH user can only update himself - User1
        """
        with app.test_request_context():
            self._blend()
            with mixer.ctx(commit=False):
                someone = mixer.blend(User)

            payload = {
                "data": {
                    "type": "user",
                    "id": "2",
                    "attributes": {
                            "name": someone.name,
                            "password": someone.password,
                            "email": someone.email,
                            "hour": someone.hour,
                            "latitude": someone.latitude,
                            "longitude": someone.longitude,
                            "observation-radius": someone.observation_radius,
                            "secid": someone.secid,
                            "statpic-id": someone.statpic_id
                    }
                }
            }

            payload["data"]["id"] = "1"
            payload["data"]["attributes"]["name"] = someone.name = "someone_1"
            payload["data"]["attributes"]["email"] = someone.email = "someone_1@email.email"
            self._send_patch("/v1/users/1", payload=payload, code=403, user=self.user1)

            payload["data"]["id"] = "2"
            payload["data"]["attributes"]["name"] = someone.name = "someone_2"
            payload["data"]["attributes"]["email"] = someone.email = "someone_2@email.email"
            response = self._send_patch("/v1/users/2", payload=payload, code=200, user=self.user1)
            self._check_user_with_private(response, someone, skip_check=['times'])

            payload["data"]["id"] = "3"
            payload["data"]["attributes"]["name"] = someone.name = "someone_3"
            payload["data"]["attributes"]["email"] = someone.email = "someone_3@email.email"
            self._send_patch("/v1/users/3", payload=payload, code=403, user=self.user1)

            payload["data"]["id"] = "4"
            payload["data"]["attributes"]["name"] = someone.name = "someone_4"
            payload["data"]["attributes"]["email"] = someone.email = "someone_4@email.email"
            self._send_patch("/v1/users/4", payload=payload, code=403, user=self.user1)

    def test_patch_same_username_admin(self):
        """
        Check User: PATCH username uniqueness - Admin
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": "1",
                    "attributes": {
                        "name": "someone"
                    }
                }
            }
            self._send_patch("/v1/users/1", payload=payload, code=200, user=self.admin)
            payload["data"]["id"] = "2"
            self._send_patch("/v1/users/2", payload=payload, code=422, user=self.admin)
            payload["data"]["id"] = "3"
            self._send_patch("/v1/users/3", payload=payload, code=422, user=self.admin)
            payload["data"]["id"] = "4"
            self._send_patch("/v1/users/4", payload=payload, code=422, user=self.admin)

    def test_patch_same_username_user1(self):
        """
        Check User: PATCH username uniqueness - User1
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": self.user1.id,
                    "attributes": {
                        "name": self.user2.name
                    }
                }
            }
            self._send_patch("/v1/users/%s" % self.user1.id, payload=payload, code=422, user=self.user1)

    def test_patch_same_email_admin(self):
        """
        Check User: PATCH email uniqueness - Admin
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": "1",
                    "attributes": {
                        "email": "someone@email.email"
                    }
                }
            }
            self._send_patch("/v1/users/1", payload=payload, code=200, user=self.admin)
            payload["data"]["id"] = "2"
            self._send_patch("/v1/users/2", payload=payload, code=422, user=self.admin)
            payload["data"]["id"] = "3"
            self._send_patch("/v1/users/3", payload=payload, code=422, user=self.admin)
            payload["data"]["id"] = "4"
            self._send_patch("/v1/users/4", payload=payload, code=422, user=self.admin)

    def test_patch_same_email_user1(self):
        """
        Check User: PATCH email uniqueness - User1
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": self.user1.id,
                    "attributes": {
                        "email": self.user2.email
                    }
                }
            }
            self._send_patch("/v1/users/%s" % self.user1.id, payload=payload, code=422, user=self.user1)

    def test_patch_id_must_match(self):
        """
        Check User: PATCH id must match
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": "1",
                    "attributes": {
                        "secid": "some ultra secret string"
                    }
                }
            }
            self._send_patch("/v1/users/1", payload=payload, code=200, user=self.admin)
            self._send_patch("/v1/users/2", payload=payload, code=400, user=self.admin)
            self._send_patch("/v1/users/3", payload=payload, code=400, user=self.admin)
            self._send_patch("/v1/users/4", payload=payload, code=400, user=self.admin)

    def test_patch_hour_is_read_only(self):
        """
        Check User: PATCH hour is read only
        """
        with app.test_request_context():
            self._blend()
            payload = {
                "data": {
                    "type": "user",
                    "id": "1",
                    "attributes": {
                        "hour": 42
                    }
                }
            }
            self._send_patch("/v1/users/1", payload=payload, code=200, user=self.admin)
            obj = safe_query(db, User, 'id', '1', 'user_id')
            self.assertNotEqual(obj.hour, 42)

    def test_delete_list(self):
        """
        Check User: DELETE list
        """
        with app.test_request_context():
            self._blend()
            self._send_delete("/v1/users", code=405)
            self._send_delete("/v1/users", code=405, user=self.admin)
            self._send_delete("/v1/users", code=405, user=self.user1)
            self._send_delete("/v1/users", code=405, user=self.user2)

    def test_delete_anonymous(self):
        """
        Check User: DELETE Anonymous
        """
        with app.test_request_context():
            self._blend()
            self._send_delete("/v1/users/1", code=401)
            self._send_delete("/v1/users/2", code=401)
            self._send_delete("/v1/users/3", code=401)
            self._send_delete("/v1/users/4", code=401)

    def test_delete_admin(self):
        """
        Check User: DELETE Admin
        """
        with app.test_request_context():
            self._blend()
            # self._send_delete("/v1/users/1", code=200, user=self.admin)
            self._send_delete("/v1/users/2", code=200, user=self.admin)
            self._send_delete("/v1/users/3", code=200, user=self.admin)
            self._send_delete("/v1/users/4", code=404, user=self.admin)

    def test_delete_user1(self):
        """
        Check User: DELETE User1
        """
        with app.test_request_context():
            self._blend()
            self._send_delete("/v1/users/1", code=403, user=self.user1)
            self._send_delete("/v1/users/2", code=403, user=self.user1)
            self._send_delete("/v1/users/3", code=403, user=self.user1)
            self._send_delete("/v1/users/4", code=403, user=self.user1)

    def test_delete_user2(self):
        """
        Check User: DELETE User2
        """
        with app.test_request_context():
            self._blend()
            self._send_delete("/v1/users/1", code=403, user=self.user2)
            self._send_delete("/v1/users/2", code=403, user=self.user2)
            self._send_delete("/v1/users/3", code=403, user=self.user2)
            self._send_delete("/v1/users/4", code=403, user=self.user2)
