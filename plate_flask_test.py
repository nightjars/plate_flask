import unittest
import requests
import json

host = 'http://192.168.1.99:5000'
login_url = '/auth'
recent_vehicles_url = '/api/vehicle/recent'
search_vehicles_url = '/api/vehicle/search'
search_vehicles_params = {'start_date': None, 'end_date': None, 'plate_substring': None,
                          'note': None, 'include_thubnails': False}
#delete_vehicle_url = '/api/vehicle/delete'
set_vehicle_note_url = '/api/vehicle/set_note'
vehicle_details_url = '/api/vehicle/details/{}'
#create_alert_url = '/api/vehicle/alert/create'
#delete_alert_url = '/api/vehicle/alert/delete'
#get_alerts_param = '/api/vehicle/alert/get/{}'
#get_alerts_all = '/api/vehicle/alert/get'

class MyTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def login_admin(self):
        return requests.post(host + login_url, json={'username': 'admin', 'password': 'admin'}).json()

    def login_read_only(self):
        return requests.post(host + login_url, json={'username': 'view', 'password': 'view'}).json()

    def login_write(self):
        return requests.post(host + login_url, json={'username': 'write', 'password': 'write'}).json()

    def login_bad(self):
        return requests.post(host + login_url, json={'username': 'baduser', 'password': 'badpass'}).json()

    def auth_header(self, user):
        return {'Authorization': 'JWT {}'.format(user['access_token'])}

    def test_fail_bad_login(self):
        bad_user = self.login_bad()
        self.assertTrue('access_token' not in bad_user)

    def test_login_admin(self):
        admin_user = self.login_admin()
        self.assertTrue('access_token' in admin_user)

    def test_login_read(self):
        read_user = self.login_read_only()
        self.assertTrue('access_token' in read_user)

    def test_login_write(self):
        write_user = self.login_write()
        self.assertTrue('access_token' in write_user)

    def test_recent_vehicles(self):
        user = self.login_read_only()
        recent = requests.get(host + recent_vehicles_url, headers=self.auth_header(user)).json()
        self.assertTrue('counts' in recent)

    def test_search_vehicles_and_get_details(self):
        user = self.login_read_only()
        search = requests.get(host + search_vehicles_url, params=search_vehicles_params,
                              headers=self.auth_header(user)).json()
        self.assertTrue('results' in search)
        self.assertTrue(len(search['results']) > 0)
        vehicle = search['results'][0]
        details = requests.get(host + vehicle_details_url.format(vehicle['id']), headers=self.auth_header(user)).json()
        self.assertTrue(vehicle['plate'] == details['plate'])
        self.assertTrue('event_list' in details)

    def test_set_note(self):
        user = self.login_read_only()
        search = requests.get(host + search_vehicles_url, params=search_vehicles_params,
                              headers=self.auth_header(user)).json()
        vehicle = search['results'][0]
        details = requests.get(host + vehicle_details_url.format(vehicle['id']), headers=self.auth_header(user)).json()
        old_note = details['note']

        requests.post(host + set_vehicle_note_url, headers=self.auth_header(user),
                      json={'id': details['id'], 'note': 'Test Note'})

if __name__ == '__main__':
    unittest.main()
