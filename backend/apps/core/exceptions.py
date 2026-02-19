from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(response_exc, context):
    response = exception_handler(response_exc, context)
    if response is not None:
        response.data['status_code'] = response.status_code
    return response
