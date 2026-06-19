import json
import logging
from openai import OpenAI, APIError, RateLimitError, APITimeoutError, AuthenticationError
from flask import current_app

logger = logging.getLogger(__name__)


def get_client():
    api_key = current_app.config.get('OPENAI_API_KEY', '')
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def analyze_task(title, description=''):
    client = get_client()
    if client is None:
        return {
            'priority': 'medium',
            'category': 'General',
            'estimated_hours': 1,
            'summary': 'AI غير متاح — راجع إعدادات API key',
        }
    prompt = (
        f'Analyze this task and return JSON:\n'
        f'Title: {title}\n'
        f'Description: {description}\n\n'
        f'Respond with JSON: {{"priority": "low|medium|high", '
        f'"category": "suggested category", '
        f'"estimated_hours": number, '
        f'"summary": "one line summary"}}'
    )
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            timeout=30,
        )
        return json.loads(response.choices[0].message.content)
    except AuthenticationError:
        logger.error('OpenAI authentication failed: invalid API key')
        raise
    except RateLimitError:
        logger.warning('OpenAI rate limit exceeded')
        raise
    except APITimeoutError:
        logger.error('OpenAI request timed out')
        raise
    except APIError as e:
        logger.error(f'OpenAI API error: {e}')
        raise
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse OpenAI response: {e}')
        raise ValueError('Invalid JSON response from AI')


def suggest_distribution(tasks_data):
    client = get_client()
    if client is None:
        return {'suggestions': [], 'message': 'AI غير متاح — راجع إعدادات API key'}
    prompt = (
        f'Given these unassigned tasks, suggest a distribution:\n'
        f'{tasks_data}\n\n'
        f'Respond with JSON: {{"suggestions": ['
        f'{{"task_title": "...", "suggested_priority": "...", "rationale": "..."}}]}}'
    )
    try:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            timeout=30,
        )
        return json.loads(response.choices[0].message.content)
    except (AuthenticationError, RateLimitError, APITimeoutError, APIError) as e:
        logger.error(f'OpenAI suggest_distribution failed: {e}')
        raise
