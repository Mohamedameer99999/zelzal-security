from unittest.mock import patch
import json


def test_ai_analyze_requires_auth(client):
    resp = client.post('/ai/analyze', json={'title': 'test'})
    assert resp.status_code == 302


def test_ai_analyze_missing_title(logged_in_client):
    resp = logged_in_client.post('/ai/analyze', json={})
    assert resp.status_code == 400
    assert b'title is required' in resp.data


def test_ai_analyze_empty_title(logged_in_client):
    resp = logged_in_client.post('/ai/analyze', json={'title': ''})
    assert resp.status_code == 400
    assert b'title cannot be empty' in resp.data


def test_ai_analyze_long_title(logged_in_client):
    resp = logged_in_client.post('/ai/analyze', json={'title': 'x' * 201})
    assert resp.status_code == 400
    assert b'title too long' in resp.data


def test_ai_suggest_requires_auth(client):
    resp = client.get('/ai/suggest')
    assert resp.status_code == 302


def test_ai_suggest_no_tasks(logged_in_client):
    resp = logged_in_client.get('/ai/suggest')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['suggestions'] == []


@patch('app.ai.routes.analyze_task')
def test_ai_analyze_success(mock_analyze, logged_in_client):
    mock_analyze.return_value = {
        'priority': 'high',
        'category': 'Development',
        'estimated_hours': 4,
        'summary': 'Critical bug fix',
    }
    resp = logged_in_client.post('/ai/analyze', json={'title': 'Fix login bug'})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['priority'] == 'high'
    assert data['category'] == 'Development'
