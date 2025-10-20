"""
Custom error views for LIMS Backend API
Returns JSON responses for errors instead of HTML
"""
from django.http import JsonResponse


def handler404(request, exception=None):
    """Handle 404 errors with JSON response"""
    return JsonResponse({
        'status': 'error',
        'code': 404,
        'message': 'Not Found',
        'detail': 'The requested resource was not found on this server.',
        'path': request.path
    }, status=404)


def handler500(request):
    """Handle 500 errors with JSON response"""
    return JsonResponse({
        'status': 'error',
        'code': 500,
        'message': 'Internal Server Error',
        'detail': 'An internal server error occurred. Please try again later.'
    }, status=500)


def handler403(request, exception=None):
    """Handle 403 errors with JSON response"""
    return JsonResponse({
        'status': 'error',
        'code': 403,
        'message': 'Forbidden',
        'detail': 'You do not have permission to access this resource.'
    }, status=403)


def handler400(request, exception=None):
    """Handle 400 errors with JSON response"""
    return JsonResponse({
        'status': 'error',
        'code': 400,
        'message': 'Bad Request',
        'detail': 'The server could not understand the request.'
    }, status=400)

