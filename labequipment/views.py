from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import Equipment
# from authentication.decorators import any_authenticated_user
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


def safe_datetime_format(dt_value):
    """
    Safely format datetime value to ISO format string
    Handles both datetime objects and string values
    """
    if not dt_value:
        return ''
    
    # If it's already a string, return as is
    if isinstance(dt_value, str):
        return dt_value
    
    # If it's a datetime object, convert to ISO format
    try:
        return dt_value.isoformat()
    except (AttributeError, TypeError):
        return str(dt_value) if dt_value else ''


# ============= EQUIPMENT CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
# @any_authenticated_user
def equipment_list(request):
    """
    List all equipment or create a new equipment
    GET: Returns list of all equipment
    POST: Creates a new equipment
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get query parameters for filtering
            status_filter = request.GET.get('status', '')
            verification_due = request.GET.get('verification_due', '')
            search = request.GET.get('search', '')
            
            # Build query
            query = {'is_active': True}
            
            if status_filter:
                query['status'] = status_filter
            
            if verification_due.lower() == 'true':
                # Find equipment where verification is due
                query['verification_due__lt'] = datetime.now()
            
            if search:
                from mongoengine import Q
                search_query = Q(equipment_name__icontains=search) | \
                              Q(equipment_serial__icontains=search) | \
                              Q(remarks__icontains=search)
                equipment_queryset = Equipment.objects(search_query & Q(is_active=True)).order_by('-created_at')
            else:
                equipment_queryset = Equipment.objects(**query).order_by('-created_at')
            
            # Get equipment with pagination
            paginated_equipment, total_records = paginate_queryset(equipment_queryset, page, limit)
            
            data = []
            for equipment in paginated_equipment:
                data.append({
                    'id': str(equipment.id),
                    'equipment_name': equipment.equipment_name,
                    'equipment_serial': equipment.equipment_serial,
                    'status': equipment.status,
                    'last_verification': safe_datetime_format(equipment.last_verification),
                    'verification_due': safe_datetime_format(equipment.verification_due),
                    'created_by': equipment.created_by,
                    'updated_by': equipment.updated_by,
                    'remarks': equipment.remarks,
                    'is_active': equipment.is_active,
                    'created_at': safe_datetime_format(equipment.created_at),
                    'updated_at': safe_datetime_format(equipment.updated_at),
                    'is_verification_due': equipment.is_verification_due(),
                    'days_until_verification_due': equipment.days_until_verification_due()
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
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['equipment_name', 'equipment_serial', 'created_by']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Check if equipment serial already exists
            if Equipment.objects(equipment_serial=data['equipment_serial'], is_active=True).count() > 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Equipment with this serial number already exists'
                }, status=400)
            
            # Parse datetime fields if provided
            last_verification = None
            verification_due = None
            
            if data.get('last_verification'):
                try:
                    last_verification = datetime.fromisoformat(data['last_verification'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid last_verification date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            if data.get('verification_due'):
                try:
                    verification_due = datetime.fromisoformat(data['verification_due'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid verification_due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            equipment = Equipment(
                equipment_name=data['equipment_name'],
                equipment_serial=data['equipment_serial'],
                status=data.get('status', 'Active'),
                last_verification=last_verification,
                verification_due=verification_due,
                created_by=data['created_by'],
                updated_by=data.get('updated_by', data['created_by']),
                remarks=data.get('remarks', '')
            )
            equipment.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Equipment created successfully',
                'data': {
                    'id': str(equipment.id),
                    'equipment_name': equipment.equipment_name,
                    'equipment_serial': equipment.equipment_serial,
                    'status': equipment.status
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
# @any_authenticated_user
def equipment_detail(request, equipment_id):
    """
    Get, update, or delete a specific equipment by ObjectId
    GET: Returns equipment details
    PUT: Updates equipment information
    DELETE: Deletes the equipment (soft delete)
    """
    try:
        try:
            equipment = Equipment.objects.get(id=ObjectId(equipment_id), is_active=True)
        except (Equipment.DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Equipment not found'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(equipment.id),
                    'equipment_name': equipment.equipment_name,
                    'equipment_serial': equipment.equipment_serial,
                    'status': equipment.status,
                    'last_verification': safe_datetime_format(equipment.last_verification),
                    'verification_due': safe_datetime_format(equipment.verification_due),
                    'created_by': equipment.created_by,
                    'updated_by': equipment.updated_by,
                    'remarks': equipment.remarks,
                    'is_active': equipment.is_active,
                    'created_at': safe_datetime_format(equipment.created_at),
                    'updated_at': safe_datetime_format(equipment.updated_at),
                    'is_verification_due': equipment.is_verification_due(),
                    'days_until_verification_due': equipment.days_until_verification_due()
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Check if equipment serial is being changed and if it already exists
                if 'equipment_serial' in data and data['equipment_serial'] != equipment.equipment_serial:
                    if Equipment.objects(equipment_serial=data['equipment_serial'], is_active=True).count() > 0:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Equipment with this serial number already exists'
                        }, status=400)
                
                # Update fields if provided
                update_fields = [
                    'equipment_name', 'equipment_serial', 'status', 
                    'created_by', 'updated_by', 'remarks'
                ]
                
                for field in update_fields:
                    if field in data:
                        setattr(equipment, field, data[field])
                
                # Handle datetime fields
                if 'last_verification' in data:
                    if data['last_verification']:
                        try:
                            equipment.last_verification = datetime.fromisoformat(data['last_verification'].replace('Z', '+00:00'))
                        except ValueError:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Invalid last_verification date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                            }, status=400)
                    else:
                        equipment.last_verification = None
                
                if 'verification_due' in data:
                    if data['verification_due']:
                        try:
                            equipment.verification_due = datetime.fromisoformat(data['verification_due'].replace('Z', '+00:00'))
                        except ValueError:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Invalid verification_due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                            }, status=400)
                    else:
                        equipment.verification_due = None
                
                equipment.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Equipment updated successfully',
                    'data': {
                        'id': str(equipment.id),
                        'equipment_name': equipment.equipment_name,
                        'equipment_serial': equipment.equipment_serial,
                        'status': equipment.status,
                        'updated_at': safe_datetime_format(equipment.updated_at)
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
            # Soft delete by setting is_active to False
            equipment.is_active = False
            equipment.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Equipment deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
# @any_authenticated_user
def equipment_search(request):
    """
    Search equipment by various criteria with pagination
    Query parameters:
    - equipment_name: Search by equipment name (partial match)
    - equipment_serial: Search by equipment serial (partial match)
    - status: Filter by status
    - verification_due: Filter by verification due (true/false)
    - created_by: Filter by creator
    - page: Page number for pagination
    - limit: Items per page
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get query parameters
        equipment_name = request.GET.get('equipment_name', '')
        equipment_serial = request.GET.get('equipment_serial', '')
        status = request.GET.get('status', '')
        verification_due = request.GET.get('verification_due', '')
        created_by = request.GET.get('created_by', '')
        
        # Build query
        query = {'is_active': True}
        
        if equipment_name:
            query['equipment_name__icontains'] = equipment_name
        
        if equipment_serial:
            query['equipment_serial__icontains'] = equipment_serial
        
        if status:
            query['status'] = status
        
        if verification_due.lower() == 'true':
            query['verification_due__lt'] = datetime.now()
        
        if created_by:
            query['created_by__icontains'] = created_by
        
        # Get equipment with pagination
        equipment_queryset = Equipment.objects(**query).order_by('-created_at')
        paginated_equipment, total_records = paginate_queryset(equipment_queryset, page, limit)
        
        data = []
        for equipment in paginated_equipment:
            data.append({
                'id': str(equipment.id),
                'equipment_name': equipment.equipment_name,
                'equipment_serial': equipment.equipment_serial,
                'status': equipment.status,
                'last_verification': safe_datetime_format(equipment.last_verification),
                'verification_due': safe_datetime_format(equipment.verification_due),
                'created_by': equipment.created_by,
                'remarks': equipment.remarks,
                'is_verification_due': equipment.is_verification_due(),
                'days_until_verification_due': equipment.days_until_verification_due()
            })
        
        # Create paginated response
        response_data = create_pagination_response(data, total_records, page, limit)
        
        return JsonResponse({
            'status': 'success',
            **response_data,
            'filters_applied': {
                'equipment_name': equipment_name,
                'equipment_serial': equipment_serial,
                'status': status,
                'verification_due': verification_due,
                'created_by': created_by
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
# @any_authenticated_user
def equipment_stats(request):
    """
    Get equipment statistics
    """
    try:
        # Count total active equipment
        total_equipment = Equipment.objects(is_active=True).count()
        
        # Count by status
        status_stats = {}
        for status in ['Active', 'Inactive', 'Maintenance', 'Out of Service', 'Calibration Required']:
            count = Equipment.objects(is_active=True, status=status).count()
            status_stats[status] = count
        
        # Count equipment with verification due
        verification_due_count = Equipment.objects(
            is_active=True, 
            verification_due__lt=datetime.now()
        ).count()
        
        # Count equipment created by month
        monthly_stats = Equipment.objects(is_active=True).aggregate([
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$created_at'},
                        'month': {'$month': '$created_at'}
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.year': -1, '_id.month': -1}}
        ])
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_equipment': total_equipment,
                'status_distribution': status_stats,
                'verification_due_count': verification_due_count,
                'monthly_creation_stats': list(monthly_stats)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
# @any_authenticated_user
def equipment_verification_due(request):
    """
    Get equipment that has verification due
    """
    try:
        equipment_list = Equipment.objects(
            is_active=True,
            verification_due__lt=datetime.now()
        ).order_by('verification_due')
        
        data = []
        for equipment in equipment_list:
            data.append({
                'id': str(equipment.id),
                'equipment_name': equipment.equipment_name,
                'equipment_serial': equipment.equipment_serial,
                'status': equipment.status,
                'last_verification': safe_datetime_format(equipment.last_verification),
                'verification_due': safe_datetime_format(equipment.verification_due),
                'created_by': equipment.created_by,
                'remarks': equipment.remarks,
                'days_overdue': abs(equipment.days_until_verification_due()) if equipment.days_until_verification_due() else 0
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)