"""
Settings for the Django XLSForm Validator app.

This module provides default settings and allows for user configuration
through the Django settings.py file.
"""

from django.conf import settings

MAX_FILE_SIZE = getattr(settings, 'XLSFORM_VALIDATOR_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB default

TEMP_DIR = getattr(settings, 'XLSFORM_VALIDATOR_TEMP_DIR', '/tmp')

REST_FRAMEWORK = getattr(settings, 'XLSFORM_VALIDATOR_REST_FRAMEWORK', {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
})

MEDIA_URL = getattr(settings, 'XLSFORM_VALIDATOR_MEDIA_URL', '/media/')
MEDIA_ROOT = getattr(settings, 'XLSFORM_VALIDATOR_MEDIA_ROOT', None)

STATIC_URL = getattr(settings, 'XLSFORM_VALIDATOR_STATIC_URL', '/static/')

EXAMPLE_FILES_DIR = getattr(settings, 'XLSFORM_VALIDATOR_EXAMPLE_FILES_DIR', 'test_data')
