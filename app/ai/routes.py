import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.tasks.models import Task
from app.ai.service import analyze_task, suggest_distribution
from app.core.rate_limit import rate_limit

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/analyze', methods=['POST'])
@login_required
@rate_limit(max_requests=20, window_seconds=60)
def analyze():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'title is required'}), 400
    title = data['title'].strip()
    if not title:
        return jsonify({'error': 'title cannot be empty'}), 400
    if len(title) > 200:
        return jsonify({'error': 'title too long (max 200 chars)'}), 400
    try:
        result = analyze_task(title, data.get('description', ''))
        logger.info(f'User {current_user.id} analyzed task: {title[:50]}')
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.exception(f'AI analysis failed for user {current_user.id}')
        return jsonify({'error': 'AI service unavailable'}), 503


@ai_bp.route('/suggest', methods=['GET'])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def suggest():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    if not tasks:
        return jsonify({'message': 'No tasks to analyze', 'suggestions': []}), 200
    tasks_data = [
        {'title': t.title, 'status': t.status, 'priority': t.priority}
        for t in tasks
    ]
    try:
        result = suggest_distribution(str(tasks_data))
        logger.info(f'User {current_user.id} requested AI suggestions')
        return jsonify(result)
    except Exception as e:
        logger.exception(f'AI suggestion failed for user {current_user.id}')
        return jsonify({'error': 'AI service unavailable'}), 503
