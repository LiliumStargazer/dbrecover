import unittest
import json
from app import app

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_handle_dump_success(self):
        payload = {
            "db_path": "/Users/alghisi/Desktop/22493/AndBk24/AndBk.s3db",
            "db_prod_path": "/Users/alghisi/Desktop/22493/AndBk08/ProdDbTouch.s3db"
        }
        response = self.app.post('/recover', data=json.dumps(payload), content_type='application/json')
        print("responsae data: ", response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['result'], 0)

    def test_handle_dump_no_data(self):
        response = self.app.post('/recover', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], "Dati JSON non forniti")

    def test_handle_dump_error(self):
        payload = {
            "db_path": "invalid_path",
            "db_prod_path": "invalid_path"
        }
        response = self.app.post('/recover', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json)

if __name__ == '__main__':
    unittest.main()