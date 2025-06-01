#!/usr/bin/env python
"""Test script to verify Django FileField compatibility."""

import os
import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import io

if not settings.configured:
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework',
            'django_xlsform_validator',
        ],
        SECRET_KEY='test-key-for-filefield-test',
        USE_TZ=True,
    )
    django.setup()

from django_xlsform_validator.validation import XLSFormValidator

def test_django_filefield_pattern():
    """Test the pattern similar to user's Django FileField usage."""
    validator = XLSFormValidator()
    
    with open("django_xlsform_validator/test_data/test_xlsform.xlsx", "rb") as f:
        xlsform_content = f.read()
    
    with open("django_xlsform_validator/test_data/valid_spreadsheet.xlsx", "rb") as f:
        spreadsheet_content = f.read()
    
    print("Testing with SimpleUploadedFile objects...")
    xlsform_file = SimpleUploadedFile("test_xlsform.xlsx", xlsform_content)
    spreadsheet_file = SimpleUploadedFile("valid_spreadsheet.xlsx", spreadsheet_content)
    
    assert validator.parse_xlsform(xlsform_file), "Failed to parse XLSForm"
    result = validator.validate_spreadsheet(spreadsheet_file)
    assert result['is_valid'], f"Validation failed: {result.get('errors', [])}"
    print("✓ SimpleUploadedFile test passed")
    
    validator = XLSFormValidator()
    xlsform_bytesio = io.BytesIO(xlsform_content)
    spreadsheet_bytesio = io.BytesIO(spreadsheet_content)
    
    print("Testing with BytesIO objects...")
    assert validator.parse_xlsform(xlsform_bytesio), "Failed to parse XLSForm from BytesIO"
    result = validator.validate_spreadsheet(spreadsheet_bytesio)
    assert result['is_valid'], f"Validation failed: {result.get('errors', [])}"
    print("✓ BytesIO test passed")
    
    print("All tests passed! BytesIO file handling is working correctly.")

if __name__ == "__main__":
    test_django_filefield_pattern()
