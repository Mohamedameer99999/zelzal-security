import time
import logging
from functools import wraps
from flask import request, jsonify, session

logger = logging.getLogger(__name__)


def rate_limit(max_requests=30, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = f'rate_limit_{request.endpoint}_{request.remote_addr}'
            now = time.time()
            history = session.get(key, [])
            history = [t for t in history if now - t < window_seconds]
            if len(history) >= max_requests:
                logger.warning(f'Rate limit exceeded for {request.remote_addr} on {request.endpoint}')
                return jsonify({'error': 'Too many requests. Please wait.'}), 429
            history.append(now)
            session[key] = history
            return f(*args, **kwargs)
        return wrapped
    return decorator
