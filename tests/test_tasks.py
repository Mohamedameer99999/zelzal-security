def test_task_list_requires_login(client):
    resp = client.get('/tasks/', follow_redirects=True)
    assert b'Sign In' in resp.data


def test_empty_task_list(logged_in_client):
    resp = logged_in_client.get('/tasks/')
    assert resp.status_code == 200
    assert b'No tasks found' in resp.data


def test_create_task(logged_in_client):
    resp = logged_in_client.post('/tasks/create', data={
        'title': 'Buy groceries',
        'description': 'Milk, eggs, bread',
        'status': 'pending',
        'priority': 'medium',
        'category': 'Personal',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Buy groceries' in resp.data


def test_create_task_empty_title(logged_in_client):
    resp = logged_in_client.post('/tasks/create', data={
        'title': '',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'This field is required' in resp.data


def test_edit_task(logged_in_client, db, user, sample_task):
    resp = logged_in_client.post(f'/tasks/{sample_task.id}/edit', data={
        'title': 'Updated title',
        'status': 'done',
        'priority': 'high',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Updated title' in resp.data


def test_edit_nonexistent_task(logged_in_client):
    resp = logged_in_client.get('/tasks/999/edit')
    assert resp.status_code == 404


def test_delete_task(logged_in_client, db, user, sample_task):
    resp = logged_in_client.post(f'/tasks/{sample_task.id}/delete', follow_redirects=True)
    assert resp.status_code == 200
    assert b'Task deleted' in resp.data


def test_cannot_access_other_users_task(logged_in_client, db):
    from app.auth.models import User
    other = User(username='other', email='other@example.com')
    other.set_password('pass')
    db.session.add(other)
    db.session.commit()
    from app.tasks.models import Task
    t = Task(title='Other task', user_id=other.id)
    db.session.add(t)
    db.session.commit()
    resp = logged_in_client.get(f'/tasks/{t.id}/edit')
    assert resp.status_code == 404


def test_filter_by_status(logged_in_client, db, user):
    from app.tasks.models import Task
    for s in ['pending', 'in_progress', 'done']:
        db.session.add(Task(title=f'Task {s}', status=s, user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/?status=done')
    assert b'Task done' in resp.data
    assert b'Task pending' not in resp.data


def test_export_pdf_requires_login(client):
    resp = client.get('/tasks/export-pdf')
    assert resp.status_code == 302


def test_export_pdf_empty(logged_in_client):
    resp = logged_in_client.get('/tasks/export-pdf')
    assert resp.status_code == 200
    assert resp.mimetype == 'application/pdf'
    assert resp.content_length > 0


def test_export_pdf_with_tasks(logged_in_client, db, user):
    from app.tasks.models import Task
    db.session.add(Task(title='Task A', status='pending', priority='high', user_id=user.id))
    db.session.add(Task(title='Task B', status='done', priority='low', user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/export-pdf')
    assert resp.status_code == 200
    assert resp.mimetype == 'application/pdf'
    assert resp.content_length > 500


def test_create_task_with_due_date(logged_in_client):
    resp = logged_in_client.post('/tasks/create', data={
        'title': 'Task with deadline',
        'due_date': '2026-12-31',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Task with deadline' in resp.data
    assert b'2026-12-31' in resp.data


def test_create_task_empty_due_date(logged_in_client):
    resp = logged_in_client.post('/tasks/create', data={
        'title': 'No deadline',
        'due_date': '',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'No deadline' in resp.data


def test_overdue_shown_in_list(logged_in_client, db, user):
    from datetime import date
    from app.tasks.models import Task
    t = Task(title='Overdue task', status='pending', due_date=date(2020, 1, 1), user_id=user.id)
    db.session.add(t)
    db.session.commit()
    resp = logged_in_client.get('/tasks/')
    assert b'Overdue task' in resp.data
    assert b'exclamation-triangle' in resp.data


def test_search_filters_by_title(logged_in_client, db, user):
    from app.tasks.models import Task
    db.session.add(Task(title='Buy milk', user_id=user.id))
    db.session.add(Task(title='Walk dog', user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/?q=milk')
    assert b'Buy milk' in resp.data
    assert b'Walk dog' not in resp.data


def test_search_tasks_by_description(logged_in_client, db, user):
    from app.tasks.models import Task
    db.session.add(Task(title='Fix bug', description='the login page crashes', user_id=user.id))
    db.session.add(Task(title='Add feature', user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/?q=crashes')
    assert b'Fix bug' in resp.data
    assert b'Add feature' not in resp.data


def test_board_requires_login(client):
    resp = client.get('/tasks/board')
    assert resp.status_code == 302


def test_board_shows_columns(logged_in_client, db, user):
    from app.tasks.models import Task
    db.session.add(Task(title='A', status='pending', user_id=user.id))
    db.session.add(Task(title='B', status='in_progress', user_id=user.id))
    db.session.add(Task(title='C', status='done', user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/board')
    assert resp.status_code == 200
    assert b'Pending' in resp.data
    assert b'In Progress' in resp.data
    assert b'Done' in resp.data


def test_move_task(logged_in_client, db, user, sample_task):
    resp = logged_in_client.post(f'/tasks/{sample_task.id}/move', json={'status': 'done'})
    assert resp.status_code == 200
    assert sample_task.status == 'done'


def test_move_task_invalid_status(logged_in_client, sample_task):
    resp = logged_in_client.post(f'/tasks/{sample_task.id}/move', json={'status': 'invalid'})
    assert resp.status_code == 400


def test_move_task_missing_body(logged_in_client, sample_task):
    resp = logged_in_client.post(f'/tasks/{sample_task.id}/move', json={})
    assert resp.status_code == 400


def test_move_nonexistent_task(logged_in_client):
    resp = logged_in_client.post('/tasks/999/move', json={'status': 'done'})
    assert resp.status_code == 404


def test_export_pdf_respects_filters(logged_in_client, db, user):
    from app.tasks.models import Task
    db.session.add(Task(title='Pending one', status='pending', priority='medium', user_id=user.id))
    db.session.add(Task(title='Done one', status='done', priority='low', user_id=user.id))
    db.session.commit()
    resp = logged_in_client.get('/tasks/export-pdf?status=done')
    assert resp.status_code == 200
    assert resp.mimetype == 'application/pdf'
    assert resp.content_length > 200
