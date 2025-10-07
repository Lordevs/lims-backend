from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from .models import User, RefreshToken
from .jwt_utils import (
    generate_access_token, 
    generate_refresh_token, 
    verify_access_token, 
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    cleanup_expired_tokens
)


# ============= AUTHENTICATION ENDPOINTS =============

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    User login endpoint
    POST: Authenticate user and return access & refresh tokens
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Required field "{field}" is missing or empty'
                }, status=400)
        
        username = data['username']
        password = data['password']
        
        # Find user by username or email
        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username, is_active=True)
            except User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid username/email or password'
                }, status=401)
        
        # Check password
        if not user.check_password(password):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username/email or password'
            }, status=401)
        
        # Check if user is verified
        if not user.is_verified:
            return JsonResponse({
                'status': 'error',
                'message': 'Account not verified. Please contact administrator.'
            }, status=401)
        
        # Update last login
        user.last_login = datetime.now()
        user.save()
        
        # Generate tokens
        access_token = generate_access_token(user)
        refresh_token, refresh_expires = generate_refresh_token(user)
        
        # Clean up expired tokens
        cleanup_expired_tokens()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 900,  # 15 minutes in seconds
                'refresh_expires_in': 604800,  # 7 days in seconds
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'is_active': user.is_active,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Login failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """
    User registration endpoint
    POST: Create new user with role
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Required field "{field}" is missing or empty'
                }, status=400)
        
        # Validate role
        valid_roles = ['admin', 'project_coordinator', 'lab_engg']
        if data['role'] not in valid_roles:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid role. Must be one of: {", ".join(valid_roles)}'
            }, status=400)
        
        # Validate password strength
        password = data['password']
        if len(password) < 8:
            return JsonResponse({
                'status': 'error',
                'message': 'Password must be at least 8 characters long'
            }, status=400)
        
        # Check if username already exists
        if User.objects(username=data['username']).count() > 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Username already exists'
            }, status=400)
        
        # Check if email already exists
        if User.objects(email=data['email']).count() > 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Email already exists'
            }, status=400)
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            is_active=True,
            is_verified=True  # Auto-verify for now, can be changed to require email verification
        )
        
        # Set password
        user.set_password(password)
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'User created successfully',
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat()
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
    """
    Refresh access token endpoint
    POST: Generate new access token using refresh token
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'refresh_token' not in data or not data['refresh_token']:
            return JsonResponse({
                'status': 'error',
                'message': 'Refresh token is required'
            }, status=400)
        
        refresh_token = data['refresh_token']
        
        # Verify refresh token
        refresh_token_obj = verify_refresh_token(refresh_token)
        if not refresh_token_obj:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired refresh token'
            }, status=401)
        
        # Check if user is still active
        user = refresh_token_obj.user
        if not user.is_active:
            return JsonResponse({
                'status': 'error',
                'message': 'User account is deactivated'
            }, status=401)
        
        # Generate new access token
        access_token = generate_access_token(user)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Token refreshed successfully',
            'data': {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 900  # 15 minutes in seconds
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Token refresh failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
    """
    User logout endpoint
    POST: Revoke refresh token
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'refresh_token' not in data or not data['refresh_token']:
            return JsonResponse({
                'status': 'error',
                'message': 'Refresh token is required'
            }, status=400)
        
        refresh_token = data['refresh_token']
        
        # Revoke refresh token
        if revoke_refresh_token(refresh_token):
            return JsonResponse({
                'status': 'success',
                'message': 'Logged out successfully'
            }, status=200)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid refresh token'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Logout failed: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def verify_token(request):
    """
    Verify access token endpoint
    GET: Verify if access token is valid
    """
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'status': 'error',
                'message': 'Authorization header missing or invalid'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        payload = verify_access_token(token)
        if not payload:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=401)
        
        # Get user details
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
        
        return JsonResponse({
            'status': 'success',
            'message': 'Token is valid',
            'data': {
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'is_active': user.is_active
                },
                'token_info': {
                    'expires_at': datetime.fromtimestamp(payload['exp']).isoformat(),
                    'issued_at': datetime.fromtimestamp(payload['iat']).isoformat()
                }
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Token verification failed: {str(e)}'
        }, status=500)


# ============= USER MANAGEMENT ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET"])
def user_list(request):
    """
    List all users endpoint
    GET: Get list of all users (Admin only)
    """
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'status': 'error',
                'message': 'Authorization header missing or invalid'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_access_token(token)
        if not payload:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=401)
        
        # Check if user is admin
        if payload['role'] != 'admin':
            return JsonResponse({
                'status': 'error',
                'message': 'Admin access required'
            }, status=403)
        
        # Get all users
        users = User.objects.all().order_by('-created_at')
        
        data = []
        for user in users:
            data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Users retrieved successfully',
            'data': data,
            'total': len(data)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to retrieve users: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def user_detail(request, user_id):
    """
    Get user detail endpoint
    GET: Get specific user details
    """
    try:
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'status': 'error',
                'message': 'Authorization header missing or invalid'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_access_token(token)
        if not payload:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=401)
        
        # Check if user is admin or requesting their own data
        if payload['role'] != 'admin' and payload['user_id'] != user_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Access denied'
            }, status=403)
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'User not found'
            }, status=404)
        
        return JsonResponse({
            'status': 'success',
            'message': 'User details retrieved successfully',
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to retrieve user details: {str(e)}'
        }, status=500)