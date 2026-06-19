import logging
from datetime import date
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from fpdf import FPDF
from flask_login import login_required, current_user
from flask_babel import _
from app.tasks.models import Task
from app.tasks.forms import TaskForm
from app.core.extensions import db

logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__, template_folder='../templates/tasks')


@tasks_bp.route('/')
@login_required
def list():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    q = request.args.get('q', '').strip()
    query = Task.query.filter_by(user_id=current_user.id)
    if q:
        query = query.filter(
            Task.title.ilike(f'%{q}%') | Task.description.ilike(f'%{q}%')
        )
    if status in dict(Task.STATUS_CHOICES):
        query = query.filter_by(status=status)
    if priority in dict(Task.PRIORITY_CHOICES):
        query = query.filter_by(priority=priority)
    tasks = query.order_by(Task.updated_at.desc()).all()
    today = date.today()
    return render_template('tasks/list.html', tasks=tasks, today=today)


@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data.strip(),
            description=(form.description.data or '').strip(),
            status=form.status.data,
            priority=form.priority.data,
            category=(form.category.data or '').strip(),
            due_date=form.due_date.data,
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        logger.info(f'User {current_user.id} created task {task.id}')
        flash(_('Task created.'), 'success')
        return redirect(url_for('tasks.list'))
    return render_template('tasks/create.html', form=form)


@tasks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        form.populate_obj(task)
        task.title = task.title.strip()
        task.category = task.category.strip()
        db.session.commit()
        logger.info(f'User {current_user.id} updated task {task.id}')
        flash(_('Task updated.'), 'success')
        return redirect(url_for('tasks.list'))
    return render_template('tasks/edit.html', form=form, task=task)


@tasks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    logger.info(f'User {current_user.id} deleted task {id}')
    flash(_('Task deleted.'), 'success')
    return redirect(url_for('tasks.list'))


@tasks_bp.route('/board')
@login_required
def board():
    today = date.today()
    pending = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_PENDING).order_by(Task.updated_at.desc()).all()
    in_progress = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_IN_PROGRESS).order_by(Task.updated_at.desc()).all()
    done = Task.query.filter_by(user_id=current_user.id, status=Task.STATUS_DONE).order_by(Task.updated_at.desc()).all()
    return render_template('tasks/board.html', **{
        'pending': pending, 'in_progress': in_progress, 'done': done, 'today': today,
    })


@tasks_bp.route('/<int:id>/move', methods=['POST'])
@login_required
def move(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'status is required'}), 400
    if data['status'] not in dict(Task.STATUS_CHOICES):
        return jsonify({'error': 'invalid status'}), 400
    task.status = data['status']
    db.session.commit()
    logger.info(f'User {current_user.id} moved task {id} to {data["status"]}')
    return jsonify({'ok': True})


@tasks_bp.route('/export-pdf')
@login_required
def export_pdf():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    query = Task.query.filter_by(user_id=current_user.id)
    if status in dict(Task.STATUS_CHOICES):
        query = query.filter_by(status=status)
    if priority in dict(Task.PRIORITY_CHOICES):
        query = query.filter_by(priority=priority)
    tasks = query.order_by(Task.updated_at.desc()).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'Task Report', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(10)

    for i, task in enumerate(tasks, 1):
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, f'{i}. {task.title}', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 10)
        status_label = dict(Task.STATUS_CHOICES).get(task.status, task.status)
        priority_label = dict(Task.PRIORITY_CHOICES).get(task.priority, task.priority)
        pdf.cell(0, 6, f'Status: {status_label}  |  Priority: {priority_label}', new_x='LMARGIN', new_y='NEXT')
        if task.category:
            pdf.cell(0, 6, f'Category: {task.category}', new_x='LMARGIN', new_y='NEXT')
        if task.description:
            desc = task.description[:200]
            pdf.multi_cell(0, 6, f'Description: {desc}')
        if task.due_date:
            pdf.cell(0, 6, f'Due: {task.due_date.strftime("%Y-%m-%d")}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 6, f'Created: {task.created_at.strftime("%Y-%m-%d %H:%M")}', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    logger.info(f'User {current_user.id} exported {len(tasks)} tasks to PDF')
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name='tasks_report.pdf')
