"""
Views for the XLSForm validator API.
"""

import base64
import io
import os
import uuid

from django.http import FileResponse, Http404
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from . import app_settings
from .serializers import SpreadsheetValidationSerializer, ValidationResultSerializer
from .validation import XLSFormValidator


class SpreadsheetValidationViewSet(viewsets.ViewSet):
    """
    API endpoint for validating spreadsheet data against an XLSForm.
    """

    http_method_names = ["get", "post", "options", "head", "trace"]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        """
        Validate a spreadsheet against an XLSForm.

        Request body:
        - xlsform_file: The XLSForm file containing the form definition
        - spreadsheet_file: The spreadsheet file to validate

        Returns:
        - 200 OK with {"result": "valid"} if the spreadsheet is valid
        - 200 OK with {"result": "invalid", "errors": [...]} if the spreadsheet is invalid
        - 400 Bad Request if the request is invalid
        """
        serializer = SpreadsheetValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        xlsform_file = serializer.validated_data["xlsform_file"]
        spreadsheet_file = serializer.validated_data["spreadsheet_file"]
        generate_xml = serializer.validated_data.get("generate_xml", False)
        version = serializer.validated_data.get("version", "1.0")

        validator = XLSFormValidator()

        if not validator.parse_xlsform(xlsform_file, version):
            return Response(
                {
                    "result": "invalid",
                    "errors": [
                        {
                            "line": 0,
                            "column": 0,
                            "error_type": "error_parsing",
                            "error_explanation": "Failed to parse XLSForm file. Make sure it contains 'survey' and 'choices' sheets.",
                            "question_name": "",
                        }
                    ],
                },
                status=status.HTTP_200_OK,
            )

        result = validator.validate_spreadsheet(spreadsheet_file)

        if result["is_valid"]:
            response_data = {"result": "valid"}

            if generate_xml:
                try:
                    response_data["xml_files"] = list(map(lambda x: x["xml"], result["valides"]))
                except Exception as e:
                    return Response(
                        {
                            "result": "invalid",
                            "errors": [
                                {
                                    "line": 0,
                                    "column": 0,
                                    "error_type": "xml_generation_error",
                                    "error_explanation": f"Failed to generate XML: {str(e)}",
                                    "question_name": "",
                                }
                            ],
                        },
                        status=status.HTTP_200_OK,
                    )
        else:
            validation_id = str(uuid.uuid4())
            highlighted_file_buffer = validator.create_highlighted_excel(
                spreadsheet_file, result["errors"]
            )

            highlighted_file_buffer.seek(0)
            file_data_b64 = base64.b64encode(highlighted_file_buffer.read()).decode(
                "utf-8"
            )

            request.session[f"validation_{validation_id}"] = {
                "file_data": file_data_b64,
                "errors": result["errors"],
            }

            response_data = {
                "result": "invalid",
                "errors": result["errors"],
                "download_id": validation_id,
            }

        result_serializer = ValidationResultSerializer(data=response_data)
        result_serializer.is_valid(raise_exception=True)

        return Response(result_serializer.validated_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def form(self, request):
        """
        Render the web UI form for file upload and validation.
        """
        return render(request, "django_xlsform_validator/validate.html")

    @action(detail=False, methods=["get"])
    def download(self, request):
        """
        Download the highlighted Excel file with errors.
        """
        validation_id = request.GET.get("id")
        if not validation_id:
            raise Http404("Download ID not provided")

        session_key = f"validation_{validation_id}"
        validation_data = request.session.get(session_key)

        if not validation_data or "file_data" not in validation_data:
            raise Http404("File not found or expired")

        file_data = base64.b64decode(validation_data["file_data"])
        file_buffer = io.BytesIO(file_data)

        response = FileResponse(
            file_buffer,
            as_attachment=True,
            filename="highlighted_spreadsheet.xlsx",
        )
        return response

    @action(detail=False, methods=["get"])
    def download_example(self, request):
        """
        Download example files for testing the validator.
        """
        file_type = request.GET.get("file")

        example_dir = getattr(app_settings, "EXAMPLE_FILES_DIR", "test_data")

        if file_type == "xlsform":
            file_path = os.path.join(example_dir, "file_active_validation_excel.xlsx")
            filename = "example_xlsform.xlsx"
        elif file_type == "spreadsheet":
            file_path = os.path.join(
                example_dir, "sample_validation_data_file_active.xlsx"
            )
            filename = "example_spreadsheet.xlsx"
        else:
            raise Http404("Invalid file type")

        if not os.path.exists(file_path):
            raise Http404("Example file not found")

        response = FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=filename,
        )
        return response
