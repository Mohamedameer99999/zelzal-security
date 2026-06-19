import pytest
from app import create_app
from app.core.extensions import db as _db
from app.auth.models import User
from app.tasks.models import Task


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'OPENAI_API_KEY': 'test-key',
        'SECRET_KEY': 'test-secret-key-for-testing',
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def auth_headers(client):
    return {}


@pytest.fixture
def user(db):
    u = User(username='testuser', email='test@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def logged_in_client(client, user):
    # Login with correct field names (username, not email)
    resp = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123',
    }, follow_redirects=True)
    assert resp.status_code == 200, f"Login failed: {resp.status_code}"
    return client


@pytest.fixture
def sample_task(db, user):
    t = Task(title='Test Task', description='A test task', user_id=user.id)
    db.session.add(t)
    db.session.commit()
    return t
