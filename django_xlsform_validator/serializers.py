"""
Serializers for the XLSForm validator API.
"""

from rest_framework import serializers

from . import app_settings
from .validation import ERROR_VALUE_REQUIRED, ERROR_CONSTRAINT_UNSATISFIED


class SpreadsheetValidationSerializer(serializers.Serializer):
    """
    Serializer for validating spreadsheet data against an XLSForm.
    """

    xlsform_file = serializers.FileField(
        help_text="The XLSForm file containing the form definition."
    )
    spreadsheet_file = serializers.FileField(
        help_text="The spreadsheet file to validate against the XLSForm."
    )
    generate_xml = serializers.BooleanField(
        default=False,
        help_text="Whether to generate XML files from the validated data.",
    )
    version = serializers.CharField(
        default="1.0",
        required=False,
        help_text="Version string for generated XML files.",
    )

    def validate_xlsform_file(self, value):
        """
        Validate that the uploaded file is a valid Excel file.
        """
        if not value.name.endswith((".xls", ".xlsx")):
            raise serializers.ValidationError(
                "XLSForm file must be an Excel file (.xls or .xlsx)"
            )

        if value.size > app_settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"XLSForm file size must be less than {app_settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        return value

    def validate_spreadsheet_file(self, value):
        """
        Validate that the uploaded file is a valid Excel file.
        """
        if not value.name.endswith((".xls", ".xlsx", ".csv")):
            raise serializers.ValidationError(
                "Spreadsheet file must be an Excel file (.xls or .xlsx) or CSV file (.csv)"
            )

        if value.size > app_settings.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"Spreadsheet file size must be less than {app_settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        return value


class ValidationErrorSerializer(serializers.Serializer):
    """
    Serializer for validation error objects.
    """

    line = serializers.IntegerField(
        help_text="Line number in the original spreadsheet."
    )
    column = serializers.IntegerField(
        help_text="Column number in the original spreadsheet."
    )
    error_type = serializers.CharField(
        help_text=f"Type of error: 'type_mismatch', '{ERROR_CONSTRAINT_UNSATISFIED}', or '{ERROR_VALUE_REQUIRED}'."
    )
    error_explanation = serializers.CharField(
        help_text="Human-readable explanation of the error."
    )
    question_name = serializers.CharField(
        help_text="The question name for the column with the error."
    )
    constraint_message = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Custom constraint message from XLSForm if available."
    )


class ValidationResultSerializer(serializers.Serializer):
    """
    Serializer for validation results.
    """

    result = serializers.CharField(help_text="Validation result: 'valid' or 'invalid'.")
    errors = ValidationErrorSerializer(
        many=True,
        required=False,
        help_text="List of validation errors if result is 'invalid'.",
    )
    download_id = serializers.CharField(
        required=False,
        help_text="ID for downloading the highlighted Excel file with errors.",
    )
    xml_files = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of generated XML files if generate_xml was requested.",
    )
