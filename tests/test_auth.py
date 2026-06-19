def test_register_page(client):
    resp = client.get('/auth/register')
    assert resp.status_code == 200
    assert b'Register' in resp.data


def test_register(client):
    resp = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
    })
    assert resp.status_code == 302


def test_register_duplicate_email(client, user):
    resp = client.post('/auth/register', data={
        'username': 'another',
        'email': 'test@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
    })
    assert resp.status_code == 200
    assert b'Email already registered' in resp.data


def test_login_page(client):
    resp = client.get('/auth/login')
    assert resp.status_code == 200
    assert b'Sign In' in resp.data


def test_login_success(client, user):
    resp = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Logout' in resp.data


def test_login_failure(client):
    resp = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'wrong',
    })
    assert resp.status_code == 200
    assert b'Invalid username or password' in resp.data


def test_logout(client, user):
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123',
    })
    resp = client.get('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Sign In' in resp.data


def test_forgot_password_page(client):
    resp = client.get('/auth/forgot-password')
    assert resp.status_code == 200


def test_authenticated_redirects_to_dashboard(client, user):
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123',
    })
    resp = client.get('/auth/login', follow_redirects=True)
    assert b'Dashboard' in resp.data
