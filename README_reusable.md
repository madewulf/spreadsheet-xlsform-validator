# Django XLSForm Validator

A Django app for validating spreadsheet data against XLSForm specifications.

## Features

- Validate spreadsheet data (Excel, CSV) against XLSForm specifications
- Check for type mismatches, constraint violations, and required values
- Provide detailed error reports with line and column information
- Generate highlighted Excel files showing validation errors
- Web UI for file upload and validation
- REST API for programmatic validation

## Installation

```bash
pip install django-xlsform-validator
```

Or install from source:

```bash
git clone https://github.com/madewulf/spreadsheet-xlsform-validator.git
cd spreadsheet-xlsform-validator
pip install -e .
```

## Quick Start

1. Add "django_xlsform_validator" to your INSTALLED_APPS setting:

```python
INSTALLED_APPS = [
    ...
    'django_xlsform_validator',
]
```

2. Include the django_xlsform_validator URLconf in your project urls.py:

```python
urlpatterns = [
    ...
    path('validator/', include('django_xlsform_validator.urls', namespace='django_xlsform_validator')),
]
```

3. Run `python manage.py collectstatic` to collect static files.

4. Start the development server and visit http://127.0.0.1:8000/validator/validate/form/ to use the validation form.

## Configuration

You can customize the app's behavior by adding the following settings to your project's settings.py:

```python
# Maximum file size for uploads (in bytes)
XLSFORM_VALIDATOR_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB default

# Temporary directory for file processing
XLSFORM_VALIDATOR_TEMP_DIR = '/tmp'

# REST Framework settings
XLSFORM_VALIDATOR_REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# Media settings
XLSFORM_VALIDATOR_MEDIA_URL = '/media/'
XLSFORM_VALIDATOR_MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static settings
XLSFORM_VALIDATOR_STATIC_URL = '/static/'
```

## API Usage

### REST API

The app provides a REST API for validating spreadsheets programmatically:

```python
import requests

url = 'http://127.0.0.1:8000/validator/validate/'
files = {
    'xlsform_file': open('path/to/xlsform.xlsx', 'rb'),
    'spreadsheet_file': open('path/to/data.xlsx', 'rb')
}
response = requests.post(url, files=files)
result = response.json()

if result['result'] == 'valid':
    print('Validation successful!')
else:
    print('Validation failed:')
    for error in result['errors']:
        print(f"Line {error['line']}, Column {error['column']}: {error['error_explanation']}")
```

### Python API

You can also use the validator directly in your Python code:

```python
from django_xlsform_validator.validation import XLSFormValidator

validator = XLSFormValidator()
validator.parse_xlsform(xlsform_file)
result = validator.validate_spreadsheet(spreadsheet_file)

if result['is_valid']:
    print('Validation successful!')
else:
    print('Validation failed:')
    for error in result['errors']:
        print(f"Line {error['line']}, Column {error['column']}: {error['error_explanation']}")
```

## XLSForm Specification Limitations

This validator implements core XLSForm functionality but does not yet support all features of the XLSForm specification. The following features are **not currently implemented**:

| Feature | Status | Description |
|---------|--------|-------------|
| `relevant` column | ❌ Not implemented | Conditional logic to show/hide questions based on other responses |
| `calculation` column | ❌ Not implemented | Automatic calculation of values based on other question responses |
| Advanced constraint expressions | ⚠️ Partial | Complex XPath expressions may not be fully supported |
| Repeat groups | ❌ Not implemented | Repeating sections of questions |
| Advanced question types | ⚠️ Partial | Some specialized question types may not be validated |

## Libraries Used

This validator uses the following libraries:
- **pyxform**: For parsing XLSForm files and converting them to internal format
- **elementpath (XPath1Parser)**: For validating XPath constraint expressions
- **pandas & openpyxl**: For processing Excel and CSV files

## Try the Validator Online

You can test this validator online at: https://data-validator.bluesquare.org/

## License

This project is licensed under the MIT License - see the LICENSE file for details.
