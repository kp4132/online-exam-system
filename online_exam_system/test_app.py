"""
Automated Integration Tests for Online Exam and Quiz System
Verifies:
1. Student demo vs blocked admin demo login
2. Manual admin login with private credentials
3. Single concurrent session login enforcement
4. Admin change password flow (custom private password)
5. 5 Subject quizzes (HTML, CSS, C++, Ethical Hacking, Mobile Programming)
"""

import unittest
from app import app
from database import init_db

class OnlineExamSystemTestCase(unittest.TestCase):
    def setUp(self):
        init_db()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_homepage_and_login_render(self):
        """Test home page and login page load properly."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Online Exam & Quiz System', res.data)

        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In', res.data)

    def test_02_demo_admin_is_blocked(self):
        """Verify that demo login for admin is completely disabled."""
        res = self.client.get('/demo-login/admin', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Admin Demo Login has been disabled', res.data)
        self.assertIn(b'Sign In', res.data)

    def test_03_admin_manual_login_and_single_session_enforcement(self):
        """Test manual admin login and verify single-session concurrent login policy."""
        # 1. Login with Admin credentials on Client 1
        client1 = app.test_client()
        res1 = client1.post('/login', data={'identifier': 'admin@exam.com', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b'Instructor & Admin Control Center', res1.data)

        # 2. Open a second session / device for the same admin on Client 2
        client2 = app.test_client()
        res2 = client2.post('/login', data={'identifier': 'admin@exam.com', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'Instructor & Admin Control Center', res2.data)

        # 3. Client 1 (first session) attempts to navigate again -> MUST BE LOGGED OUT
        res1_again = client1.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(res1_again.status_code, 200)
        self.assertIn(b'Single Login Policy', res1_again.data)
        self.assertIn(b'Sign In', res1_again.data)

    def test_04_admin_change_password_to_private(self):
        """Verify that admin can set their own private password and previous password stops working."""
        admin_client = app.test_client()
        # Login with default Admin@123
        admin_client.post('/login', data={'identifier': 'admin@exam.com', 'password': 'Admin@123'}, follow_redirects=True)
        
        # Change password to new private password
        new_private_pass = "MySecretAdminPass#99"
        change_res = admin_client.post('/admin/change-password', data={
            'current_password': 'Admin@123',
            'new_password': new_private_pass,
            'confirm_password': new_private_pass
        }, follow_redirects=True)
        self.assertEqual(change_res.status_code, 200)
        self.assertIn(b'Admin password updated successfully', change_res.data)

        # Logout
        admin_client.get('/logout')

        # Attempt to login with OLD password -> MUST FAIL
        fail_res = admin_client.post('/login', data={'identifier': 'admin@exam.com', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertIn(b'Invalid email/username or password', fail_res.data)

        # Attempt to login with NEW private password -> MUST SUCCEED
        success_res = admin_client.post('/login', data={'identifier': 'admin@exam.com', 'password': new_private_pass}, follow_redirects=True)
        self.assertEqual(success_res.status_code, 200)
        self.assertIn(b'Instructor & Admin Control Center', success_res.data)

    def test_05_subject_quizzes_present(self):
        """Test that HTML, CSS, C++, Ethical Hacking, and Mobile Programming quizzes exist."""
        res = self.client.get('/demo-login/student', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        self.assertIn(b'HTML5 &amp; Web Markup Essentials', res.data)
        self.assertIn(b'CSS3 Styling &amp; Modern Layouts', res.data)
        self.assertIn(b'C++ Programming &amp; OOP Architecture', res.data)
        self.assertIn(b'Ethical Hacking &amp; Cybersecurity Essentials', res.data)
        self.assertIn(b'Mobile Programming &amp; App Architecture', res.data)

    def test_06_certificate_access(self):
        """Test certificate rendering for passed attempt."""
        self.client.get('/demo-login/student', follow_redirects=True)
        res = self.client.get('/exam/certificate/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Certificate of Achievement', res.data)
        self.assertIn(b'VERIFIED CREDENTIAL', res.data)

if __name__ == '__main__':
    unittest.main()
