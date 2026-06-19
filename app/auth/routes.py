import logging
from datetime import datetime, timezone
from secrets import token_urlsafe
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import _
from app.auth.models import User
from app.auth.forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from app.core.extensions import db

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            logger.info(f'User {user.id} logged in')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        flash(_('Invalid username or password.'), 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        logger.info(f'User {user.id} registered')
        flash(_('Account created! You can now log in.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    logger.info(f'User {user_id} logged out')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.reset_token = token_urlsafe(32)
            user.reset_token_expires = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour + 1
            )
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=user.reset_token, _external=True)
            logger.info(f'Password reset link for {user.email}: {reset_url}')
            current_app.logger.info(f'Password reset requested for {user.email}')
        flash(_('If that email is registered, a reset link has been sent.'), 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expires < datetime.now(timezone.utc):
        flash(_('Invalid or expired reset token.'), 'danger')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        logger.info(f'Password reset completed for user {user.id}')
        flash(_('Password reset successful! You can now log in.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
