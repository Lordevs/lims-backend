from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.datastructures import MultiValueDict
import json
import os
import uuid
from datetime import datetime
from .models import Welder
from mongoengine.errors import DoesNotExist, ValidationError
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


def handle_image_upload(image_file, welder_id=None):
    """
    Handle image upload with proper file naming and storage
    """
    if not image_file:
        return None
    
    # Generate unique filename
    file_extension = os.path.splitext(image_file.name)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        raise ValueError("Invalid image format. Allowed: jpg, jpeg, png, gif, webp")
    
    unique_filename = f"welder_{welder_id or uuid.uuid4()}_{uuid.uuid4().hex[:8]}{file_extension}"
    
    # Create media directory if it doesn't exist
    media_dir = os.path.join(settings.MEDIA_ROOT, 'welders')
    os.makedirs(media_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(media_dir, unique_filename)
    with default_storage.open(file_path, 'wb') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)
    
    # Return relative path for database storage
    return os.path.join('welders', unique_filename)


def delete_old_image(image_path):
    """
    Delete old image file if it exists
    """
    if image_path and image_path != '':
        try:
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Error deleting old image: {e}")


def parse_multipart_data(request):
    """
    Parse multipart form data for PUT requests using Django's built-in utilities
    """
    if request.content_type and 'multipart/form-data' in request.content_type:
        try:
            # Use Django's built-in multipart parser with proper setup
            from django.http.multipartparser import MultiPartParser
            from django.core.files.uploadhandler import MemoryFileUploadHandler
            from django.http import QueryDict
            from io import BytesIO
            
            # Create upload handlers
            upload_handlers = [MemoryFileUploadHandler()]
            
            # Create a file-like object from the request body
            body_file = BytesIO(request.body)
            
            # Parse the multipart data
            parser = MultiPartParser(request.META, body_file, upload_handlers)
            parsed_data, files = parser.parse()
            
            # Convert QueryDict to regular dict for easier handling
            form_data = {}
            for key, value in parsed_data.items():
                if isinstance(value, list) and len(value) == 1:
                    form_data[key] = value[0]
                else:
                    form_data[key] = value
            
            return form_data, files
            
        except Exception as e:
            print(f"Error parsing multipart data: {e}")
            return {}, {}
    
    return None, None


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def welder_list(request):
    """
    List all welders or create a new welder
    GET: Returns list of all welders
    POST: Creates a new welder
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get filtering parameters
            show_inactive = request.GET.get('show_inactive', '').lower() == 'true'
            include_inactive = request.GET.get('include_inactive', '').lower() == 'true'
            
            # Build query based on filtering parameters
            if show_inactive:
                # Only show inactive welders
                welders_queryset = Welder.objects.filter(is_active=False).order_by('-updated_at')
            elif include_inactive:
                # Show both active and inactive welders
                welders_queryset = Welder.objects.all().order_by('-created_at')
            else:
                # Default: only show active welders
                welders_queryset = Welder.objects.filter(is_active=True).order_by('-created_at')
            
            paginated_welders, total_records = paginate_queryset(welders_queryset, page, limit)
            
            data = []
            for welder in paginated_welders:
                data.append({
                    'id': str(welder.id),
                    'operator_name': welder.operator_name,
                    'operator_id': welder.operator_id,
                    'iqama': welder.iqama,
                    'profile_image': welder.profile_image,
                    'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None,
                    'is_active': welder.is_active,
                    'created_at': welder.created_at.isoformat(),
                    'updated_at': welder.updated_at.isoformat()
                })
            
            # Create paginated response
            response_data = create_pagination_response(data, total_records, page, limit)
            
            return JsonResponse({
                'status': 'success',
                **response_data
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    elif request.method == 'POST':
        try:
            # Handle form data for image upload
            if request.content_type and 'multipart/form-data' in request.content_type:
                # Parse multipart form data
                parsed_data, files = parse_multipart_data(request)
                
                if parsed_data is None:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to parse multipart form data'
                    }, status=400)
                
                # Form data with file upload
                operator_name = parsed_data.get('operator_name')
                if isinstance(operator_name, list):
                    operator_name = operator_name[0]
                
                operator_id = parsed_data.get('operator_id')
                if isinstance(operator_id, list):
                    operator_id = operator_id[0]
                
                iqama = parsed_data.get('iqama')
                if isinstance(iqama, list):
                    iqama = iqama[0]
                
                is_active_value = parsed_data.get('is_active', 'true')
                if isinstance(is_active_value, list):
                    is_active_value = is_active_value[0]
                is_active = is_active_value.lower() == 'true'
                
                profile_image_file = files.get('profile_image') if files else None
                
                # Validate required fields
                if not operator_name or not operator_id or not iqama:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Required fields: operator_name, operator_id, iqama'
                    }, status=400)
                
                # Handle image upload
                profile_image_path = None
                if profile_image_file:
                    try:
                        profile_image_path = handle_image_upload(profile_image_file)
                    except ValueError as e:
                        return JsonResponse({
                            'status': 'error',
                            'message': str(e)
                        }, status=400)
                
                welder = Welder(
                    operator_name=operator_name,
                    operator_id=operator_id,
                    iqama=iqama,
                    profile_image=profile_image_path or '',
                    is_active=is_active
                )
                welder.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Welder created successfully',
                    'data': {
                        'id': str(welder.id),
                        'operator_name': welder.operator_name,
                        'operator_id': welder.operator_id,
                        'iqama': welder.iqama,
                        'profile_image': welder.profile_image,
                        'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None
                    }
                }, status=201)
            
            else:
                # JSON data (for API compatibility)
                data = json.loads(request.body)
                
                # Validate required fields
                required_fields = ['operator_name', 'operator_id', 'iqama']
                for field in required_fields:
                    if field not in data or not data[field]:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Required field "{field}" is missing or empty'
                        }, status=400)
                
                welder = Welder(
                    operator_name=data['operator_name'],
                    operator_id=data['operator_id'],
                    iqama=data['iqama'],
                    profile_image=data.get('profile_image', ''),
                    is_active=data.get('is_active', True)
                )
                welder.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Welder created successfully',
                    'data': {
                        'id': str(welder.id),
                        'operator_name': welder.operator_name,
                        'operator_id': welder.operator_id,
                        'iqama': welder.iqama,
                        'profile_image': welder.profile_image,
                        'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None
                    }
                }, status=201)
            
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Validation error: {str(e)}'
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@any_authenticated_user
def welder_detail(request, object_id):
    """
    Get, update, or delete a specific welder by ObjectId
    GET: Returns welder details
    PUT: Updates welder information
    DELETE: Deletes the welder
    """
    try:
        # Convert object_id to ObjectId
        try:
            from bson import ObjectId
            object_id = ObjectId(object_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid ObjectId format: {str(e)}'
            }, status=400)
            
        welder = Welder.objects.get(id=object_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(welder.id),
                    'operator_name': welder.operator_name,
                    'operator_id': welder.operator_id,
                    'iqama': welder.iqama,
                    'profile_image': welder.profile_image,
                    'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None,
                    'is_active': welder.is_active,
                    'created_at': welder.created_at.isoformat(),
                    'updated_at': welder.updated_at.isoformat()
                }
            })
        
        elif request.method == 'PUT':
            try:
                # Handle form data for image upload
                if request.content_type and 'multipart/form-data' in request.content_type:
                    # Parse multipart form data manually for PUT requests
                    parsed_data, files = parse_multipart_data(request)
                    
                    if parsed_data is None:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Failed to parse multipart form data'
                        }, status=400)
                    
                    # Form data with potential file upload
                    update_doc = {}
                    
                    # Handle text fields - values are already processed by parser
                    if 'operator_name' in parsed_data:
                        update_doc['operator_name'] = parsed_data['operator_name']
                    if 'operator_id' in parsed_data:
                        update_doc['operator_id'] = parsed_data['operator_id']
                    if 'iqama' in parsed_data:
                        update_doc['iqama'] = parsed_data['iqama']
                    if 'is_active' in parsed_data:
                        update_doc['is_active'] = parsed_data['is_active'].lower() == 'true'
                    
                    # Handle image upload/update
                    profile_image_file = files.get('profile_image') if files else None
                    remove_image = parsed_data.get('remove_image', 'false').lower() == 'true'
                    
                    if remove_image:
                        # Delete existing image
                        delete_old_image(welder.profile_image)
                        update_doc['profile_image'] = ''
                    elif profile_image_file:
                        # Upload new image and delete old one
                        delete_old_image(welder.profile_image)
                        try:
                            new_image_path = handle_image_upload(profile_image_file, str(welder.id))
                            update_doc['profile_image'] = new_image_path
                        except ValueError as e:
                            return JsonResponse({
                                'status': 'error',
                                'message': str(e)
                            }, status=400)
                    
                    # Add updated timestamp
                    update_doc['updated_at'] = datetime.now()
                    
                    # Update the welder
                    if update_doc:
                        welder.update(**update_doc)
                        welder.reload()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Welder updated successfully',
                        'data': {
                            'id': str(welder.id),
                            'operator_name': welder.operator_name,
                            'operator_id': welder.operator_id,
                            'iqama': welder.iqama,
                            'profile_image': welder.profile_image,
                            'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None,
                            'is_active': welder.is_active,
                            'created_at': welder.created_at.isoformat(),
                            'updated_at': welder.updated_at.isoformat()
                        }
                    })
                
                else:
                    # JSON data (for API compatibility)
                    data = json.loads(request.body)
                    
                    # Prepare update document for partial update
                    update_doc = {}
                    
                    # Only update fields that are provided in the request
                    if 'operator_name' in data:
                        update_doc['operator_name'] = data['operator_name']
                    if 'operator_id' in data:
                        update_doc['operator_id'] = data['operator_id']
                    if 'iqama' in data:
                        update_doc['iqama'] = data['iqama']
                    if 'profile_image' in data:
                        # Handle image removal via JSON
                        if data['profile_image'] == '' or data['profile_image'] is None:
                            delete_old_image(welder.profile_image)
                            update_doc['profile_image'] = ''
                        else:
                            update_doc['profile_image'] = data['profile_image']
                    if 'is_active' in data:
                        update_doc['is_active'] = data['is_active']
                    
                    # Add updated timestamp
                    update_doc['updated_at'] = datetime.now()
                    
                    # Use update() method for partial updates to avoid validation of unchanged fields
                    if update_doc:
                        welder.update(**update_doc)
                        # Refresh the welder object to get updated data
                        welder.reload()
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Welder updated successfully',
                        'data': {
                            'id': str(welder.id),
                            'operator_name': welder.operator_name,
                            'operator_id': welder.operator_id,
                            'iqama': welder.iqama,
                            'profile_image': welder.profile_image,
                            'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None,
                            'is_active': welder.is_active,
                            'created_at': welder.created_at.isoformat(),
                            'updated_at': welder.updated_at.isoformat()
                        }
                    })
                
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
        
        elif request.method == 'DELETE':
            # Soft delete: set is_active to false instead of hard delete
            welder.update(
                is_active=False,
                updated_at=datetime.now()
            )
            welder.reload()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder deactivated successfully',
                'data': {
                    'id': str(welder.id),
                    'operator_name': welder.operator_name,
                    'operator_id': welder.operator_id,
                    'iqama': welder.iqama,
                    'is_active': welder.is_active,
                    'deactivated_at': welder.updated_at.isoformat()
                }
            })
            
    except DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Welder not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def welder_search(request):
    """
    Search welders by various criteria
    Query parameters:
    - name: Search by operator name (case-insensitive)
    - operator_id: Search by operator ID
    - iqama: Search by iqama number
    - active: Filter by active status (true/false)
    """
    try:
        # Get query parameters
        name = request.GET.get('name', '')
        operator_id = request.GET.get('operator_id', '')
        iqama = request.GET.get('iqama', '')
        active = request.GET.get('active', '')
        
        # Build query
        query = {}
        if name:
            query['operator_name__icontains'] = name
        if operator_id:
            query['operator_id__icontains'] = operator_id
        if iqama:
            query['iqama__icontains'] = iqama
        if active:
            query['is_active'] = active.lower() == 'true'
        
        welders = Welder.objects.filter(**query)
        
        data = []
        for welder in welders:
            data.append({
                'id': str(welder.id),
                'operator_name': welder.operator_name,
                'operator_id': welder.operator_id,
                'iqama': welder.iqama,
                'profile_image': welder.profile_image,
                'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None,
                'is_active': welder.is_active,
                'created_at': welder.created_at.isoformat(),
                'updated_at': welder.updated_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'name': name,
                'operator_id': operator_id,
                'iqama': iqama,
                'active': active
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def welder_stats(request):
    """
    Get welder statistics
    """
    try:
        total_welders = Welder.objects.count()
        active_welders = Welder.objects.filter(is_active=True).count()
        inactive_welders = Welder.objects.filter(is_active=False).count()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_welders': total_welders,
                'active_welders': active_welders,
                'inactive_welders': inactive_welders,
                'activity_rate': round((active_welders / total_welders * 100), 2) if total_welders > 0 else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@any_authenticated_user
def welder_image_management(request, object_id):
    """
    Handle welder image upload and deletion
    POST: Upload/update image
    DELETE: Remove image
    """
    try:
        # Convert object_id to ObjectId
        try:
            from bson import ObjectId
            object_id = ObjectId(object_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid ObjectId format: {str(e)}'
            }, status=400)
            
        welder = Welder.objects.get(id=object_id)
        
        if request.method == 'POST':
            # Upload/update image
            profile_image_file = request.FILES.get('profile_image')
            
            if not profile_image_file:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No image file provided'
                }, status=400)
            
            try:
                # Delete old image if exists
                delete_old_image(welder.profile_image)
                
                # Upload new image
                new_image_path = handle_image_upload(profile_image_file, str(welder.id))
                
                # Update welder record
                welder.update(
                    profile_image=new_image_path,
                    updated_at=datetime.now()
                )
                welder.reload()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Image uploaded successfully',
                    'data': {
                        'id': str(welder.id),
                        'profile_image': welder.profile_image,
                        'profile_image_url': f"{settings.MEDIA_URL}{welder.profile_image}",
                        'updated_at': welder.updated_at.isoformat()
                    }
                })
                
            except ValueError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
        
        elif request.method == 'DELETE':
            # Remove image
            if not welder.profile_image:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No image to remove'
                }, status=400)
            
            # Delete image file
            delete_old_image(welder.profile_image)
            
            # Update welder record
            welder.update(
                profile_image='',
                updated_at=datetime.now()
            )
            welder.reload()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Image removed successfully',
                'data': {
                    'id': str(welder.id),
                    'profile_image': '',
                    'profile_image_url': None,
                    'updated_at': welder.updated_at.isoformat()
                }
            })
            
    except DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Welder not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)