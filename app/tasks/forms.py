from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from flask_babel import lazy_gettext as _l
from app.tasks.models import Task


class TaskForm(FlaskForm):
    title = StringField(_l('Title'), validators=[DataRequired(), Length(max=200)])
    description = TextAreaField(_l('Description'))
    status = SelectField(_l('Status'), choices=[
        (Task.STATUS_PENDING, _l('Pending')),
        (Task.STATUS_IN_PROGRESS, _l('In Progress')),
        (Task.STATUS_DONE, _l('Done')),
    ], default=Task.STATUS_PENDING)
    priority = SelectField(_l('Priority'), choices=[
        (Task.PRIORITY_LOW, _l('Low')),
        (Task.PRIORITY_MEDIUM, _l('Medium')),
        (Task.PRIORITY_HIGH, _l('High')),
    ], default=Task.PRIORITY_MEDIUM)
    category = StringField(_l('Category'), validators=[Length(max=100)])
    due_date = DateField(_l('Due Date'), validators=[Optional()])
    submit = SubmitField(_l('Save'))
