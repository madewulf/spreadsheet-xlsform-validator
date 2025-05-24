from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

class ModelViewSet(viewsets.ModelViewSet):
    """
    Base ModelViewSet for all API endpoints.
    """
    pass

class Paginator(PageNumberPagination):
    """
    Base paginator for all API endpoints.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class DynamicFieldsModelSerializer:
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
