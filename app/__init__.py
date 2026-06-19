import os
from flask import Flask, g, session, request, redirect, url_for, render_template, flash
from app.core.config import Config
from app.core.extensions import db, login_manager, migrate, babel
from app.core.logging import setup_logging
import json


def get_locale():
    lang = session.get('lang', request.accept_languages.best_match(['en', 'ar'], 'en'))
    return lang if lang in ['en', 'ar'] else 'en'


def load_products():
    try:
        products_path = os.path.join(os.path.dirname(__file__), '..', 'Telegram-Bot', 'products.json')
        if not os.path.exists(products_path):
            products_path = os.path.join(os.path.dirname(__file__), '..', 'Telegram-Bot-Bot', 'products.json')
        if os.path.exists(products_path):
            with open(products_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f'Error loading products: {e}')
    return []


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    setup_logging(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)

    from app.auth.routes import auth_bp
    from app.tasks.routes import tasks_bp
    from app.dashboard.routes import dashboard_bp
    from app.ai.routes import ai_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(ai_bp, url_prefix='/ai')

    @app.before_request
    def set_g_lang():
        g.lang = get_locale()

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    @app.route('/lang/<lang>')
    def set_lang(lang):
        if lang in ['en', 'ar']:
            session['lang'] = lang
        return redirect(request.referrer or url_for('dashboard.index'))

    @app.route('/buy', methods=['GET', 'POST'])
    def buy():
        products = load_products()
        if request.method == 'POST':
            product_id = request.form.get('product_id')
            product = next((p for p in products if p['id'] == product_id), None)
            if product:
                flash('Purchase request for ' + product['name'] + ' submitted! We will contact you within 24 hours.', 'success')
            else:
                flash('Product not found', 'danger')
            return redirect(url_for('buy'))
        products = load_products()
        return render_template('buy.html', products=products)

    return app
