def test_dashboard_requires_login(client):
    resp = client.get('/dashboard/', follow_redirects=True)
    assert b'Sign In' in resp.data


def test_dashboard_shows_stats(logged_in_client):
    resp = logged_in_client.get('/dashboard/')
    assert resp.status_code == 200
    assert b'Total Tasks' in resp.data
    assert b'AI Assistant' in resp.data


def test_dashboard_shows_overdue(logged_in_client, db, user):
    from datetime import date
    from app.tasks.models import Task
    t = Task(title='Late', status='pending', due_date=date(2020, 1, 1), user_id=user.id)
    db.session.add(t)
    db.session.commit()
    resp = logged_in_client.get('/dashboard/')
    assert b'Overdue' in resp.data


def test_dashboard_counts(logged_in_client, db, user, sample_task):
    resp = logged_in_client.get('/dashboard/')
    assert b'1' in resp.data
    assert b'Total Tasks' in resp.data
