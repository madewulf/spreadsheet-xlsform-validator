# Spreadsheet XLSForm Validator

A Django REST Framework API for validating spreadsheet data against XLSForm specifications.

## Overview

This API allows you to validate spreadsheet data against an XLSForm specification. It checks that:

- All column headers in the spreadsheet match question names in the XLSForm
- All values in the spreadsheet match the expected types and constraints defined in the XLSForm
- Required questions have values

## API Endpoints

### POST /api/validate/

Validates a spreadsheet against an XLSForm specification.

#### Request

- Content-Type: `multipart/form-data`
- Body:
  - `xlsform_file`: The XLSForm file (Excel format)
  - `spreadsheet_file`: The spreadsheet file to validate (Excel or CSV format)

#### Response

For valid spreadsheets:

```json
{
  "result": "valid"
}
```

For invalid spreadsheets:

```json
{
  "result": "invalid",
  "errors": [
    {
      "line": 1,
      "column": 3,
      "error_type": "type_mismatch",
      "error_explanation": "Value 'text' is not a valid integer for question 'age'",
      "question_name": "age"
    },
    ...
  ]
}
```

Error types:
- `type_mismatch`: The value does not match the expected type
- `error_constraint_unsatisfied`: The value does not satisfy the constraint
- `error_value_required`: A required value is missing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/madewulf/spreadsheet-xlsform-validator.git
cd spreadsheet-xlsform-validator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the development server:
```bash
python manage.py runserver
```

## Testing

Run the tests:
```bash
python manage.py test
```

## XLSForm Format

XLSForm is a form standard created to help simplify the authoring of forms in Excel. For more information, see [XLSForm.org](https://xlsform.org/).

An XLSForm consists of two main sheets:
- `survey`: Contains the questions and their properties
- `choices`: Contains the choices for select questions

The API validates that:
- All column headers in the spreadsheet match question names in the survey sheet
- Values for integer questions are valid integers
- Values for select_one questions are valid choices from the choices sheet
- Values for decimal questions are valid decimals
- Required questions have values
- Values satisfy any constraints defined in the XLSForm

## AWS Elastic Beanstalk Deployment

### Prerequisites

1. Install AWS CLI:
```bash
pip install awscli
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Install EB CLI:
```bash
pip install awsebcli
```

### Deployment Steps

1. Initialize Elastic Beanstalk application:
```bash
eb init --platform python-3.9 --region us-east-1
```

2. Create environment:
```bash
eb create production --database.engine postgres --database.username ebroot
```

3. Set environment variables:
```bash
eb setenv DEBUG=False SECRET_KEY=your-secret-key-here ALLOWED_HOSTS=.elasticbeanstalk.com
eb setenv DB_ENGINE=django.db.backends.postgresql DB_NAME=ebdb DB_USER=ebroot DB_PASSWORD=your-db-password DB_HOST=your-rds-endpoint DB_PORT=5432
```

4. Deploy application:
```bash
eb deploy
```

5. Open application:
```bash
eb open
```

### Environment Variables

Set these environment variables in the Elastic Beanstalk console:

- `DEBUG`: Set to `False` for production
- `SECRET_KEY`: Generate a secure secret key for Django
- `ALLOWED_HOSTS`: Set to your domain (e.g., `.elasticbeanstalk.com`)
- `DB_ENGINE`: `django.db.backends.postgresql` (recommended for production)
- `DB_NAME`: Database name (default: `ebdb`)
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password  
- `DB_HOST`: RDS endpoint
- `DB_PORT`: Database port (default: `5432`)

### Notes

- The application uses PostgreSQL in production (recommended over SQLite)
- Static files are served using WhiteNoise
- Database migrations run automatically on deployment
- A default admin user is created (username: `admin`, password: `changeme123`) - change this immediately
