import unittest
import os
import sqlite3
import shutil
from flask import Flask, send_file, redirect
from werkzeug.utils import secure_filename
from io import BytesIO
import impasse as assimp
from app import server, init_db, get_db_connection, TEMP_UPLOAD_FOLDER, TEXTURE_UPLOAD_FOLDER, convert_to_obj
import tempfile


class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the test database
        cls.db_fd, cls.db_path = tempfile.mkstemp()
        server.config['DATABASE'] = cls.db_path
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Close and remove the temporary database
        os.close(cls.db_fd)
        os.unlink(cls.db_path)
        shutil.rmtree(TEMP_UPLOAD_FOLDER)

    def setUp(self):
        self.app = server.test_client()
        self.app.testing = True

    def test_index_redirect(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dash/', response.location)

    def test_database_connection(self):
        conn = get_db_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_convert_to_obj(self):
        # Use a valid .fbx file for the test
        input_file_path = 'valid_test.fbx'  # Make sure this file exists in the project directory
        output_file_path = os.path.join(TEMP_UPLOAD_FOLDER, 'test.obj')

        try:
            convert_to_obj(input_file_path, output_file_path)
            self.assertTrue(os.path.exists(output_file_path))
        finally:
            if os.path.exists(output_file_path):
                os.remove(output_file_path)

   

if __name__ == '__main__':
    unittest.main()
