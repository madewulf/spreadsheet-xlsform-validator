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
