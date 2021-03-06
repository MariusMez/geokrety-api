import json
import pprint
import unittest
from datetime import date, datetime

import phpass
from app import current_app as app
from tests.unittests.setup_database import Setup


# https://stackoverflow.com/a/22238613/944936
def json_serial(obj):  # pragma: no cover
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError("Type %s not serializable" % type(obj))


def mock_hash_password(obj, password):
    """Mock hash_password from phpass.PasswordHash"""
    return password


def mock_check_password(obj, password_1, password_2):
    """Mock check_password from phpass.PasswordHash"""
    return password_1 == password_2


class GeokretyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Setup.create_app()
        phpass.PasswordHash.hash_password = mock_hash_password
        phpass.PasswordHash.check_password = mock_check_password

    def tearDown(self):
        Setup.drop_db()

    def _login(self, username="kumy", password="password"):
        """
        Obtain a JWT token to authenticate next requests
        """
        response = self.app.post('/auth/session',
                                 headers={
                                     'content-type': 'application/json'
                                 },
                                 data=json.dumps({
                                     "username": username,
                                     "password": password
                                 }), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Content-Type' in response.headers)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        raised = False
        try:
            data = json.loads(response.data)
        except Exception:  # pragma: no cover
            raised = True
        self.assertFalse(raised, 'Failed to decode json')
        self.assertTrue('access_token' in data)
        return data['access_token']

    def _send(self,
              method,
              endpoint,
              code=200,
              payload=None,
              user=None,
              content_type='application/vnd.api+json'):
        """
        Send a POST request to the api, and check expected response code.
        """
        if not payload:
            payload = {}

        headers = {}
        if user:
            headers['Authorization'] = \
                'JWT %s' % self._login(user.name, user.password)

        with app.test_request_context():
            response = getattr(self.app, method)(endpoint,
                                                 data=json.dumps(payload, default=json_serial),
                                                 headers=headers,
                                                 content_type=content_type)
        data = response.get_data(as_text=True)
        if response.status_code != code:  # pragma: no cover
            print("Endpoint: %s" % endpoint)
            pprint.pprint(json.dumps(payload, default=json_serial))
            pprint.pprint(data)

        self.assertEqual(response.status_code, code)
        if response.content_type in ['application/vnd.api+json', 'application/json'] and data:
            return json.loads(data)
        return data

    def _send_post(self,
                   endpoint,
                   code=200,
                   payload=None,
                   user=None,
                   content_type='application/vnd.api+json'):
        return self._send('post',
                          endpoint,
                          code=code,
                          payload=payload,
                          user=user,
                          content_type=content_type)

    def _send_get(self,
                  endpoint,
                  code=200,
                  payload=None,
                  user=None,
                  content_type='application/vnd.api+json'):
        return self._send('get',
                          endpoint,
                          code=code,
                          payload=payload,
                          user=user,
                          content_type=content_type)

    def _send_patch(self,
                    endpoint,
                    code=200,
                    payload=None,
                    user=None,
                    content_type='application/vnd.api+json'):
        return self._send('patch',
                          endpoint,
                          code=code,
                          payload=payload,
                          user=user,
                          content_type=content_type)

    def _send_delete(self,
                     endpoint,
                     code=200,
                     payload=None,
                     user=None,
                     content_type='application/vnd.api+json'):
        return self._send('delete',
                          endpoint,
                          code=code,
                          payload=payload,
                          user=user,
                          content_type=content_type)

    def assertDateTimeEqual(self, datetime_str, datetime_obj):
        if isinstance(datetime_obj, str):   # pragma: no cover
            # Check date is parsable
            raised = False
            try:
                datetime.strptime(datetime_obj, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                raised = True
            self.assertFalse(raised, 'Date is not parsable')
        else:
            self.assertEqual(datetime_str, datetime_obj.strftime("%Y-%m-%dT%H:%M:%S"))

    # def assertDateEqual(self, date_str, date_obj):
    #     if isinstance(date_obj, str):
    #         # Check date is parsable
    #         raised = False
    #         try:
    #             datetime.strptime(date_obj, "%Y-%m-%d")
    #         except Exception:  # pragma: no cover
    #             raised = True
    #         self.assertFalse(raised, 'Date is not parsable')
    #     else:
    #         self.assertEqual(date_str, date_obj.strftime("%Y-%m-%d"))

    def _check_geokret(self, data, geokret, skip_check=None, with_private=False):
        skip_check = skip_check or []
        # self.assertTrue('attributes' in data['data'])
        # attributes = data['data']['attributes']
        self.assertTrue('attributes' in data)
        attributes = data['attributes']

        self.assertTrue('name' in attributes)
        self.assertTrue('description' in attributes)
        self.assertTrue('missing' in attributes)
        self.assertTrue('distance' in attributes)
        self.assertTrue('caches-count' in attributes)
        self.assertTrue('pictures-count' in attributes)
        self.assertTrue('average-rating' in attributes)
        self.assertTrue('created-on-date-time' in attributes)
        self.assertTrue('updated-on-date-time' in attributes)

        self.assertEqual(attributes['name'], geokret.name)
        self.assertEqual(attributes['description'], geokret.description)
        self.assertEqual(attributes['missing'], geokret.missing)
        self.assertEqual(attributes['distance'], geokret.distance)
        self.assertEqual(attributes['caches-count'], geokret.caches_count)
        self.assertEqual(attributes['pictures-count'], geokret.pictures_count)
        self.assertEqual(attributes['average-rating'], geokret.average_rating)

        if 'times' not in skip_check:
            self.assertDateTimeEqual(attributes['created-on-date-time'], geokret.created_on_date_time)
            self.assertDateTimeEqual(attributes['updated-on-date-time'], geokret.updated_on_date_time)

        if with_private is not None:
            self.assertTrue('attributes' in data)
            attributes = data['attributes']

            if with_private:
                self.assertTrue('tracking-code' in attributes)
                if 'tracking-code' not in skip_check:
                    self.assertEqual(attributes['tracking-code'], geokret.tracking_code)
            else:
                self.assertFalse('tracking-code' in attributes)
