"""
Views for the XLSForm validator API.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import SpreadsheetValidationSerializer, ValidationResultSerializer
from .validation import XLSFormValidator

class SpreadsheetValidationViewSet(viewsets.ViewSet):
    """
    API endpoint for validating spreadsheet data against an XLSForm.
    """
    http_method_names = ["post", "options", "head", "trace"]
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
        
        xlsform_file = serializer.validated_data['xlsform_file']
        spreadsheet_file = serializer.validated_data['spreadsheet_file']
        
        validator = XLSFormValidator()
        
        if not validator.parse_xlsform(xlsform_file):
            return Response(
                {"result": "invalid", "errors": [{
                    "line": 0,
                    "column": 0,
                    "error_type": "error_parsing",
                    "error_explanation": "Failed to parse XLSForm file. Make sure it contains 'survey' and 'choices' sheets.",
                    "question_name": ""
                }]},
                status=status.HTTP_200_OK
            )
        
        result = validator.validate_spreadsheet(spreadsheet_file)
        
        if result['is_valid']:
            response_data = {"result": "valid"}
        else:
            response_data = {"result": "invalid", "errors": result['errors']}
        
        result_serializer = ValidationResultSerializer(data=response_data)
        result_serializer.is_valid(raise_exception=True)
        
        return Response(result_serializer.validated_data, status=status.HTTP_200_OK)
