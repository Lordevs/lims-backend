from functools import wraps
from django.http import JsonResponse
from .jwt_utils import verify_access_token
from .models import User


def jwt_required(required_roles=None):
    """
    Decorator to require JWT authentication for endpoints
    
    Args:
        required_roles (list): List of roles that can access the endpoint.
                              If None, any authenticated user can access.
    
    Usage:
        @jwt_required()  # Any authenticated user
        @jwt_required(['admin'])  # Admin only
        @jwt_required(['admin', 'project_coordinator'])  # Admin or Project Coordinator
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get token from Authorization header
                auth_header = request.META.get('HTTP_AUTHORIZATION', '')
                if not auth_header.startswith('Bearer '):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Authorization header missing or invalid. Please provide Bearer token.'
                    }, status=401)
                
                token = auth_header.split(' ')[1]
                
                # Verify token
                payload = verify_access_token(token)
                if not payload:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid or expired token'
                    }, status=401)
                
                # Get user from database
                try:
                    user = User.objects.get(id=payload['user_id'])
                    if not user.is_active:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'User account is deactivated'
                        }, status=401)
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'User not found'
                    }, status=401)
                
                # Check role permissions
                if required_roles and user.role not in required_roles:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Access denied. Required roles: {", ".join(required_roles)}'
                    }, status=403)
                
                # Add user to request for use in views
                request.user = user
                request.user_payload = payload
                
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Authentication error: {str(e)}'
                }, status=500)
        
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to require admin role for endpoints
    """
    return jwt_required(['admin'])(view_func)


def coordinator_or_admin_required(view_func):
    """
    Decorator to require project coordinator or admin role for endpoints
    """
    return jwt_required(['admin', 'project_coordinator'])(view_func)


def any_authenticated_user(view_func):
    """
    Decorator to require any authenticated user for endpoints
    """
    return jwt_required()(view_func)


def welding_operations_required(view_func):
    """
    Decorator for admin or welding coordinator
    """
    return jwt_required(['admin', 'welding_coordinator'])(view_func)