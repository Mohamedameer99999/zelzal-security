import logging
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.core.extensions import db, login_manager
from app.core.models import TimestampMixin

logger = logging.getLogger(__name__)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(128), nullable=True, unique=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship('Task', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
