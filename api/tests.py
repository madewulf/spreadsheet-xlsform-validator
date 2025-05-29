"""
Tests for the XLSForm validator API.
"""

import os
import tempfile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import pandas as pd
import openpyxl
from .validation import XLSFormValidator


class SpreadsheetValidationTests(TestCase):
    """
    Test cases for the spreadsheet validation API.
    """

    def setUp(self):
        """
        Set up test client and create test files.
        """
        self.client = APIClient()
        self.url = reverse("validate-list")

        os.makedirs("api/test_data", exist_ok=True)

        self.create_test_xlsform()
        self.create_test_xlsform_with_integer_choices()

        self.create_valid_test_spreadsheet()

        self.create_invalid_test_spreadsheet_type_mismatch()

        self.create_invalid_test_spreadsheet_constraint()

        self.create_invalid_test_spreadsheet_required()

        self.create_valid_test_spreadsheet_with_labels()

        self.create_mixed_test_spreadsheet()

        self.create_case_insensitive_test_spreadsheet()

        self.create_integer_choice_test_spreadsheet()

        self.create_excel_date_format_spreadsheet()

        self.create_test_xlsform_with_aliases()
        self.create_alias_test_spreadsheet()

        self.create_test_xlsform_with_regex_constraints()
        self.create_valid_regex_test_spreadsheet()
        self.create_invalid_regex_test_spreadsheet()

    def create_test_xlsform(self):
        """
        Create a test XLSForm file with survey and choices sheets.
        """
        wb = openpyxl.Workbook()

        survey = wb.active
        survey.title = "survey"

        survey.append(["type", "name", "label", "required", "constraint"])

        survey.append(["integer", "age", "Age", "yes", ". < 150"])
        survey.append(["select_one gender", "gender", "Gender", "yes", ""])
        survey.append(["text", "name", "Name", "yes", ""])
        survey.append(["decimal", "weight", "Weight (kg)", "no", ". > 0"])

        choices = wb.create_sheet("choices")

        choices.append(["list_name", "name", "label"])

        choices.append(["gender", "male", "Male"])
        choices.append(["gender", "female", "Female"])
        choices.append(["gender", "other", "Other"])

        wb.save("api/test_data/test_xlsform.xlsx")

    def create_valid_test_spreadsheet(self):
        """
        Create a valid test spreadsheet that matches the XLSForm.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name", "weight"])

        ws.append([25, "male", "John Doe", 75.5])
        ws.append([30, "female", "Jane Smith", 65.0])
        ws.append([45, "other", "Alex Johnson", 80.2])

        wb.save("api/test_data/valid_spreadsheet.xlsx")

    def create_invalid_test_spreadsheet_type_mismatch(self):
        """
        Create an invalid test spreadsheet with type mismatches.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name", "weight"])

        ws.append(["twenty-five", "male", "John Doe", 75.5])  # age should be integer
        ws.append([30, "unknown", "Jane Smith", 65.0])  # gender not in choices
        ws.append([45, "other", "Alex Johnson", "eighty"])  # weight should be decimal

        wb.save("api/test_data/invalid_type_mismatch.xlsx")

    def create_invalid_test_spreadsheet_constraint(self):
        """
        Create an invalid test spreadsheet with constraint violations.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name", "weight"])

        ws.append([200, "male", "John Doe", 75.5])  # age > 150
        ws.append([30, "female", "Jane Smith", -5.0])  # weight < 0
        ws.append([45, "other", "Alex Johnson", 80.2])

        wb.save("api/test_data/invalid_constraint.xlsx")

    def create_invalid_test_spreadsheet_required(self):
        """
        Create an invalid test spreadsheet with missing required values.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name", "weight"])

        ws.append([None, "male", "John Doe", 75.5])  # missing age
        ws.append([30, None, "Jane Smith", 65.0])  # missing gender
        ws.append([45, "other", None, 80.2])  # missing name

        wb.save("api/test_data/invalid_required.xlsx")

    def test_valid_spreadsheet(self):
        """
        Test validation with a valid spreadsheet.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open("api/test_data/valid_spreadsheet.xlsx", "rb") as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def test_type_mismatch_error(self):
        """
        Test validation with a spreadsheet containing type mismatches.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/invalid_type_mismatch.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "invalid")
        self.assertIn("errors", response.data)

        type_mismatch_errors = [
            e for e in response.data["errors"] if e["error_type"] == "type_mismatch"
        ]
        self.assertTrue(len(type_mismatch_errors) > 0)

    def test_constraint_unsatisfied_error(self):
        """
        Test validation with a spreadsheet containing constraint violations.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/invalid_constraint.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "invalid")
        self.assertIn("errors", response.data)

        constraint_errors = [
            e
            for e in response.data["errors"]
            if e["error_type"] == "error_constraint_unsatisfied"
        ]
        self.assertTrue(len(constraint_errors) > 0)

    def test_value_required_error(self):
        """
        Test validation with a spreadsheet containing missing required values.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open("api/test_data/invalid_required.xlsx", "rb") as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "invalid")
        self.assertIn("errors", response.data)

        required_errors = [
            e
            for e in response.data["errors"]
            if e["error_type"] == "error_value_required"
        ]
        self.assertTrue(len(required_errors) > 0)

    def create_valid_test_spreadsheet_with_labels(self):
        """
        Create a valid test spreadsheet using labels instead of names.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["Age", "Gender", "Name", "Weight (kg)"])

        ws.append([25, "male", "John Doe", 75.5])
        ws.append([30, "female", "Jane Smith", 65.0])
        ws.append([45, "other", "Alex Johnson", 80.2])

        wb.save("api/test_data/valid_spreadsheet_labels.xlsx")

    def create_mixed_test_spreadsheet(self):
        """
        Create a test spreadsheet using both names and labels.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "Gender", "name", "Weight (kg)"])

        ws.append([25, "male", "John Doe", 75.5])
        ws.append([30, "female", "Jane Smith", 65.0])
        ws.append([45, "other", "Alex Johnson", 80.2])

        wb.save("api/test_data/mixed_spreadsheet.xlsx")

    def test_valid_spreadsheet_with_labels(self):
        """
        Test validation with a spreadsheet using labels as column headers.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/valid_spreadsheet_labels.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def test_mixed_names_and_labels(self):
        """
        Test validation with a spreadsheet using both names and labels.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open("api/test_data/mixed_spreadsheet.xlsx", "rb") as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def test_highlighted_excel_download(self):
        """
        Test downloading highlighted Excel file for invalid spreadsheet.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/invalid_type_mismatch.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "invalid")
        self.assertIn("download_id", response.data)

        download_url = reverse("validate-download")
        download_response = self.client.get(
            f"{download_url}?id={response.data['download_id']}"
        )

        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(
            download_response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(
            "highlighted_spreadsheet.xlsx", download_response["Content-Disposition"]
        )

    def create_test_xlsform_with_integer_choices(self):
        """
        Create a test XLSForm file with integer choice values.
        """
        wb = openpyxl.Workbook()

        survey = wb.active
        survey.title = "survey"

        survey.append(["type", "name", "label", "required", "constraint"])

        survey.append(["integer", "age", "Age", "yes", ". < 150"])
        survey.append(["select_one status", "status", "Status", "yes", ""])
        survey.append(["text", "name", "Name", "yes", ""])
        survey.append(["decimal", "weight", "Weight (kg)", "no", ". > 0"])

        choices = wb.create_sheet("choices")

        choices.append(["list_name", "name", "label"])

        choices.append(["status", 1, "Active"])
        choices.append(["status", 2, "Inactive"])
        choices.append(["status", 3, "Pending"])

        wb.save("api/test_data/test_xlsform_integer_choices.xlsx")

    def create_integer_choice_test_spreadsheet(self):
        """
        Create a test spreadsheet with integer choice values.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "status", "name", "weight"])

        ws.append([25, 1, "John Doe", 75.5])  # Integer choice value
        ws.append([30, 2, "Jane Smith", 65.0])  # Integer choice value
        ws.append([45, 3, "Alex Johnson", 80.2])  # Integer choice value

        wb.save("api/test_data/integer_choice_spreadsheet.xlsx")

    def create_excel_date_format_spreadsheet(self):
        wb = openpyxl.Workbook()
        survey = wb.active
        survey.title = "survey"

        survey.append(["type", "name", "label", "required", "constraint"])
        survey.append(
            ["date", "last_dispensiation_date", "Last Dispensation Date", "yes", ""]
        )
        survey.append(["text", "name", "Name", "yes", ""])

        choices = wb.create_sheet("choices")
        choices.append(["list_name", "name", "label"])

        wb.save("api/test_data/test_xlsform_with_date.xlsx")

        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["last_dispensiation_date", "name"])
        ws.append(["2024-09-02 00:00:00", "John Doe"])
        ws.append(["2023-05-15 00:00:00", "Jane Smith"])

        wb.save("api/test_data/excel_date_spreadsheet.xlsx")

    def create_case_insensitive_test_spreadsheet(self):
        """
        Create a test spreadsheet with case differences in select_one values.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name", "weight"])

        ws.append([25, "MALE", "John Doe", 75.5])  # MALE instead of male
        ws.append([30, "Female", "Jane Smith", 65.0])  # Female instead of female
        ws.append([45, "oThEr", "Alex Johnson", 80.2])  # oThEr instead of other

        wb.save("api/test_data/case_insensitive_spreadsheet.xlsx")

    def test_case_insensitive_validation(self):
        """
        Test that validation works with case-insensitive matching for select_one values.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/case_insensitive_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["result"], "valid")
                self.assertNotIn("errors", response.data)

    def test_highlighted_excel_download(self):
        """
        Test downloading highlighted Excel file for invalid spreadsheet.
        """
        with open("api/test_data/test_xlsform.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/invalid_type_mismatch.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["result"], "invalid")
                self.assertIn("download_id", response.data)
                download_url = reverse("validate-download")
                download_response = self.client.get(
                    f"{download_url}?id={response.data['download_id']}"
                )

                self.assertEqual(download_response.status_code, 200)
                self.assertEqual(
                    download_response["Content-Type"],
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                self.assertIn(
                    "highlighted_spreadsheet.xlsx",
                    download_response["Content-Disposition"],
                )

    def test_integer_choice_validation(self):
        """
        Test that validation works with integer choice values.
        """
        with open(
            "api/test_data/test_xlsform_integer_choices.xlsx", "rb"
        ) as xlsform_file:
            with open(
                "api/test_data/integer_choice_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )
                self.assertEqual(response.data["result"], "valid")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertNotIn("errors", response.data)

    def create_test_xlsform_with_aliases(self):
        """
        Create a test XLSForm file with alias column in choices.
        """
        wb = openpyxl.Workbook()

        survey = wb.active
        survey.title = "survey"

        survey.append(["type", "name", "label", "required", "constraint"])
        survey.append(["integer", "age", "Age", "yes", ". < 150"])
        survey.append(["select_one gender", "gender", "Gender", "yes", ""])
        survey.append(["text", "name", "Name", "yes", ""])

        choices = wb.create_sheet("choices")
        choices.append(["list_name", "name", "label", "alias"])
        choices.append(["gender", "m", "Male", "man"])
        choices.append(["gender", "f", "Female", "woman"])
        choices.append(["gender", "o", "Other", "other_option"])

        wb.save("api/test_data/test_xlsform_with_aliases.xlsx")

    def create_alias_test_spreadsheet(self):
        """
        Create a test spreadsheet using alias values.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["age", "gender", "name"])
        ws.append([25, "man", "John Doe"])  # using alias "man" instead of "m"
        ws.append([30, "woman", "Jane Smith"])  # using alias "woman" instead of "f"
        ws.append([45, "other_option", "Alex Johnson"])  # using alias "other_option"

        wb.save("api/test_data/alias_test_spreadsheet.xlsx")

    def test_alias_validation(self):
        """
        Test that validation works with alias values.
        """
        with open("api/test_data/test_xlsform_with_aliases.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/alias_test_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def test_excel_date_format_validation(self):
        """
        Test that validation works with Excel date format (YYYY-MM-DD HH:MM:SS).
        """
        with open("api/test_data/test_xlsform_with_date.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/excel_date_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def create_test_xlsform_with_regex_constraints(self):
        """
        Create a test XLSForm with regex constraints.
        """
        wb = openpyxl.Workbook()
        survey = wb.active
        survey.title = "survey"

        survey.append(["type", "name", "label", "required", "constraint"])
        survey.append(
            [
                "text",
                "month_code",
                "Month Code",
                "yes",
                "regex(.,'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\\d{2}$')",
            ]
        )
        survey.append(
            ["text", "simple_code", "Simple Code", "yes", "regex(.,'^[a-zA-Z0-9]{2}$')"]
        )
        survey.append(["text", "name", "Name", "yes", ""])

        choices = wb.create_sheet("choices")
        choices.append(["list_name", "name", "label"])

        wb.save("api/test_data/test_xlsform_with_regex.xlsx")

    def create_valid_regex_test_spreadsheet(self):
        """
        Create a valid test spreadsheet with regex constraint values.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["month_code", "simple_code", "name"])
        ws.append(["Jan-01", "A1", "John Doe"])
        ws.append(["Feb-15", "B2", "Jane Smith"])
        ws.append(["Dec-31", "Z9", "Alex Johnson"])

        wb.save("api/test_data/valid_regex_spreadsheet.xlsx")

    def create_invalid_regex_test_spreadsheet(self):
        """
        Create an invalid test spreadsheet with regex constraint violations.
        """
        wb = openpyxl.Workbook()
        ws = wb.active

        ws.append(["month_code", "simple_code", "name"])
        ws.append(["January-01", "A1", "John Doe"])  # Invalid month format
        ws.append(["Feb-1", "ABC", "Jane Smith"])  # Invalid day format and code length
        ws.append(["13-31", "1A", "Alex Johnson"])  # Invalid month number

        wb.save("api/test_data/invalid_regex_spreadsheet.xlsx")

    def test_valid_regex_constraint_validation(self):
        """
        Test that validation passes with valid regex constraint values.
        """
        with open("api/test_data/test_xlsform_with_regex.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/valid_regex_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "valid")
        self.assertNotIn("errors", response.data)

    def test_invalid_regex_constraint_validation(self):
        """
        Test that validation fails with invalid regex constraint values.
        """
        with open("api/test_data/test_xlsform_with_regex.xlsx", "rb") as xlsform_file:
            with open(
                "api/test_data/invalid_regex_spreadsheet.xlsx", "rb"
            ) as spreadsheet_file:
                response = self.client.post(
                    self.url,
                    {
                        "xlsform_file": xlsform_file,
                        "spreadsheet_file": spreadsheet_file,
                    },
                    format="multipart",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "invalid")
        self.assertIn("errors", response.data)
        self.assertTrue(len(response.data["errors"]) > 0)
        constraint_errors = [
            e
            for e in response.data["errors"]
            if e["error_type"] == "error_constraint_unsatisfied"
        ]
        self.assertTrue(len(constraint_errors) > 0)
        
    def test_regex_validation_with_leading_zeros(self):
        """
        Test that numeric values with leading zeros are correctly validated against regex patterns.
        """
        validator = XLSFormValidator()
        validator.question_types = {'code_ets': 'text'}
        validator.constraints = {'code_ets': "regex(.,'^([0-9]{5})$')"}
        
        # Test that 1652.0 gets formatted as 01652 for 5-digit regex
        error = validator._validate_constraint(1652.0, "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error)  # Should pass validation
        
        error = validator._validate_constraint(123.0, "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error)  # Should pass validation
        
        error = validator._validate_constraint("01234", "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error)  # Should pass validation
        
    def test_regex_constraint_numeric_formatting(self):
        """
        Test specific regex constraint handling for numeric values.
        """
        validator = XLSFormValidator()
        validator.question_types = {'code_ets': 'text'}
        validator.constraints = {'code_ets': "regex(.,'^([0-9]{5})$')"}
        
        error = validator._validate_constraint(1652.0, "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error, "Validation should pass for 1652.0 with 5-digit regex pattern")
        
        error = validator._validate_constraint(123.0, "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error, "Validation should pass for 123.0 with 5-digit regex pattern")
        
        error = validator._validate_constraint("01234", "regex(.,'^([0-9]{5})$')", 'code_ets')
        self.assertIsNone(error, "Validation should pass for '01234' with 5-digit regex pattern")
