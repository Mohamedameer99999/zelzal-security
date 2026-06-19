import logging
from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app.tasks.models import Task
from app.core.extensions import db

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    try:
        today = date.today()
        total = Task.query.filter_by(user_id=current_user.id).count()
        pending = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_PENDING).count()
        in_progress = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_IN_PROGRESS).count()
        done = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_DONE).count()
        overdue = Task.query.filter(
            Task.user_id == current_user.id,
            Task.due_date.isnot(None),
            Task.due_date < today,
            Task.status != Task.STATUS_DONE,
        ).count()

        by_priority = dict(
            db.session.query(Task.priority, func.count(Task.id))
            .filter_by(user_id=current_user.id)
            .group_by(Task.priority)
            .all()
        )

        by_category = dict(
            db.session.query(Task.category, func.count(Task.id))
            .filter(Task.user_id == current_user.id, Task.category != '')
            .group_by(Task.category)
            .all()
        )

        recent = (
            Task.query.filter_by(user_id=current_user.id)
            .order_by(Task.updated_at.desc())
            .limit(5)
            .all()
        )

        logger.debug(f'Dashboard loaded for user {current_user.id}')
        return render_template('dashboard/index.html', **{
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'overdue': overdue,
            'by_priority': by_priority,
            'by_category': by_category,
            'recent': recent,
        })
    except Exception as e:
        logger.exception(f'Dashboard failed for user {current_user.id}')
        return render_template('dashboard/index.html', **{
            'total': 0, 'pending': 0, 'in_progress': 0, 'done': 0, 'overdue': 0,
            'by_priority': {}, 'by_category': {}, 'recent': [],
        })
