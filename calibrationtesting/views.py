from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from bson import ObjectId
from mongoengine.errors import DoesNotExist, ValidationError

from .models import CalibrationTest
from authentication.decorators import any_authenticated_user
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


def safe_datetime_format(dt_value):
    """
    Safely format datetime value to ISO format string
    Handles both datetime objects and string values
    """
    if not dt_value:
        return ''
    if isinstance(dt_value, str):
        return dt_value
    try:
        return dt_value.isoformat()
    except (AttributeError, TypeError):
        return str(dt_value) if dt_value else ''


# ============= CALIBRATION TEST CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def calibration_test_list(request):
    """
    List all calibration tests or create a new calibration test
    GET: Returns list of all calibration tests with pagination
    POST: Creates a new calibration test
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get query parameters for filtering
            vendor_filter = request.GET.get('vendor', '')
            equipment_filter = request.GET.get('equipment', '')
            search = request.GET.get('search', '')
            overdue_only = request.GET.get('overdue', '').lower() == 'true'
            due_soon = request.GET.get('due_soon', '').lower() == 'true'
            
            # Build query
            query = {'is_active': True}
            
            if vendor_filter:
                query['calibration_vendor__icontains'] = vendor_filter
            
            if equipment_filter:
                query['$or'] = [
                    {'equipment_name__icontains': equipment_filter},
                    {'equipment_serial__icontains': equipment_filter}
                ]
            
            if search:
                search_query = {
                    '$or': [
                        {'calibration_certification__icontains': search},
                        {'equipment_name__icontains': search},
                        {'equipment_serial__icontains': search},
                        {'calibration_vendor__icontains': search},
                        {'remarks__icontains': search}
                    ]
                }
                if '$or' in query:
                    # Combine with existing $or query
                    query = {'$and': [query, search_query]}
                else:
                    query.update(search_query)
            
            if overdue_only:
                query['calibration_due_date__lt'] = datetime.now()
            
            if due_soon:
                # Due within next 30 days
                next_30_days = datetime.now() + timedelta(days=30)
                query['calibration_due_date__lte'] = next_30_days
                query['calibration_due_date__gte'] = datetime.now()
            
            # Get calibration tests with pagination
            calibration_tests_queryset = CalibrationTest.objects(**query).order_by('-created_at')
            paginated_tests, total_records = paginate_queryset(calibration_tests_queryset, page, limit)
            
            data = []
            for test in paginated_tests:
                data.append({
                    'id': str(test.id),
                    'calibration_certification': test.calibration_certification,
                    'calibration_date': safe_datetime_format(test.calibration_date),
                    'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                    'calibration_vendor': test.calibration_vendor,
                    'created_by': test.created_by,
                    'equipment_name': test.equipment_name,
                    'equipment_serial': test.equipment_serial,
                    'is_active': test.is_active,
                    'remarks': test.remarks,
                    'updated_by': test.updated_by,
                    'created_at': safe_datetime_format(test.created_at),
                    'updated_at': safe_datetime_format(test.updated_at),
                    'is_overdue': test.is_overdue(),
                    'days_until_due': test.days_until_due(),
                    'days_since_calibration': test.days_since_calibration()
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
            required_fields = ['calibration_certification', 'calibration_date', 'calibration_due_date', 
                             'calibration_vendor', 'created_by', 'equipment_name', 'equipment_serial']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Parse datetime fields
            calibration_date = None
            calibration_due_date = None
            
            if data.get('calibration_date'):
                try:
                    calibration_date = datetime.fromisoformat(data['calibration_date'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid calibration_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            if data.get('calibration_due_date'):
                try:
                    calibration_due_date = datetime.fromisoformat(data['calibration_due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid calibration_due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            calibration_test = CalibrationTest(
                calibration_certification=data['calibration_certification'],
                calibration_date=calibration_date,
                calibration_due_date=calibration_due_date,
                calibration_vendor=data['calibration_vendor'],
                created_by=data['created_by'],
                equipment_name=data['equipment_name'],
                equipment_serial=data['equipment_serial'],
                is_active=data.get('is_active', True),
                remarks=data.get('remarks', ''),
                updated_by=data.get('updated_by', data['created_by'])
            )
            calibration_test.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Calibration test created successfully',
                'data': {
                    'id': str(calibration_test.id),
                    'calibration_certification': calibration_test.calibration_certification,
                    'equipment_name': calibration_test.equipment_name,
                    'equipment_serial': calibration_test.equipment_serial
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
def calibration_test_detail(request, test_id):
    """
    Get, update, or delete a specific calibration test by ObjectId
    GET: Returns calibration test details
    PUT: Updates calibration test information
    DELETE: Deletes the calibration test (soft delete)
    """
    try:
        try:
            test = CalibrationTest.objects.get(id=ObjectId(test_id), is_active=True)
        except (CalibrationTest.DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Calibration test not found'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(test.id),
                    'calibration_certification': test.calibration_certification,
                    'calibration_date': safe_datetime_format(test.calibration_date),
                    'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                    'calibration_vendor': test.calibration_vendor,
                    'created_by': test.created_by,
                    'equipment_name': test.equipment_name,
                    'equipment_serial': test.equipment_serial,
                    'is_active': test.is_active,
                    'remarks': test.remarks,
                    'updated_by': test.updated_by,
                    'created_at': safe_datetime_format(test.created_at),
                    'updated_at': safe_datetime_format(test.updated_at),
                    'is_overdue': test.is_overdue(),
                    'days_until_due': test.days_until_due(),
                    'days_since_calibration': test.days_since_calibration()
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Check if payload is empty
                if not data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Update fields
                update_doc = {}
                
                if 'calibration_certification' in data:
                    update_doc['calibration_certification'] = data['calibration_certification']
                
                if 'calibration_date' in data:
                    try:
                        update_doc['calibration_date'] = datetime.fromisoformat(data['calibration_date'].replace('Z', '+00:00'))
                    except ValueError:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid calibration_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                        }, status=400)
                
                if 'calibration_due_date' in data:
                    try:
                        update_doc['calibration_due_date'] = datetime.fromisoformat(data['calibration_due_date'].replace('Z', '+00:00'))
                    except ValueError:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid calibration_due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                        }, status=400)
                
                if 'calibration_vendor' in data:
                    update_doc['calibration_vendor'] = data['calibration_vendor']
                
                if 'equipment_name' in data:
                    update_doc['equipment_name'] = data['equipment_name']
                
                if 'equipment_serial' in data:
                    update_doc['equipment_serial'] = data['equipment_serial']
                
                if 'remarks' in data:
                    update_doc['remarks'] = data['remarks']
                
                if 'updated_by' in data:
                    update_doc['updated_by'] = data['updated_by']
                
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active']
                
                # Apply updates
                if update_doc:
                    test.update(**update_doc)
                    test.reload()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Calibration test updated successfully',
                    'data': {
                        'id': str(test.id),
                        'calibration_certification': test.calibration_certification,
                        'calibration_date': safe_datetime_format(test.calibration_date),
                        'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                        'calibration_vendor': test.calibration_vendor,
                        'created_by': test.created_by,
                        'equipment_name': test.equipment_name,
                        'equipment_serial': test.equipment_serial,
                        'is_active': test.is_active,
                        'remarks': test.remarks,
                        'updated_by': test.updated_by,
                        'updated_at': safe_datetime_format(test.updated_at),
                        'is_overdue': test.is_overdue(),
                        'days_until_due': test.days_until_due(),
                        'days_since_calibration': test.days_since_calibration()
                    }
                })
                
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
        
        elif request.method == 'DELETE':
            # Soft delete
            test.update(is_active=False)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Calibration test deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def calibration_test_search(request):
    """
    Search calibration tests with advanced filtering
    GET: Returns filtered calibration tests with pagination
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get search parameters
        certification = request.GET.get('certification', '')
        vendor = request.GET.get('vendor', '')
        equipment_name = request.GET.get('equipment_name', '')
        equipment_serial = request.GET.get('equipment_serial', '')
        calibration_date_from = request.GET.get('calibration_date_from', '')
        calibration_date_to = request.GET.get('calibration_date_to', '')
        due_date_from = request.GET.get('due_date_from', '')
        due_date_to = request.GET.get('due_date_to', '')
        overdue_only = request.GET.get('overdue', '').lower() == 'true'
        due_soon = request.GET.get('due_soon', '').lower() == 'true'
        
        # Build query
        query = {'is_active': True}
        
        if certification:
            query['calibration_certification__icontains'] = certification
        
        if vendor:
            query['calibration_vendor__icontains'] = vendor
        
        if equipment_name:
            query['equipment_name__icontains'] = equipment_name
        
        if equipment_serial:
            query['equipment_serial__icontains'] = equipment_serial
        
        if calibration_date_from:
            try:
                from_date = datetime.fromisoformat(calibration_date_from.replace('Z', '+00:00'))
                query['calibration_date__gte'] = from_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid calibration_date_from format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if calibration_date_to:
            try:
                to_date = datetime.fromisoformat(calibration_date_to.replace('Z', '+00:00'))
                query['calibration_date__lte'] = to_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid calibration_date_to format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if due_date_from:
            try:
                from_date = datetime.fromisoformat(due_date_from.replace('Z', '+00:00'))
                query['calibration_due_date__gte'] = from_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid due_date_from format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if due_date_to:
            try:
                to_date = datetime.fromisoformat(due_date_to.replace('Z', '+00:00'))
                query['calibration_due_date__lte'] = to_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid due_date_to format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if overdue_only:
            query['calibration_due_date__lt'] = datetime.now()
        
        if due_soon:
            # Due within next 30 days
            next_30_days = datetime.now() + timedelta(days=30)
            query['calibration_due_date__lte'] = next_30_days
            query['calibration_due_date__gte'] = datetime.now()
        
        # Get calibration tests with pagination
        calibration_tests_queryset = CalibrationTest.objects(**query).order_by('-created_at')
        paginated_tests, total_records = paginate_queryset(calibration_tests_queryset, page, limit)
        
        data = []
        for test in paginated_tests:
            data.append({
                'id': str(test.id),
                'calibration_certification': test.calibration_certification,
                'calibration_date': safe_datetime_format(test.calibration_date),
                'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                'calibration_vendor': test.calibration_vendor,
                'equipment_name': test.equipment_name,
                'equipment_serial': test.equipment_serial,
                'is_overdue': test.is_overdue(),
                'days_until_due': test.days_until_due(),
                'days_since_calibration': test.days_since_calibration(),
                'created_at': safe_datetime_format(test.created_at)
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


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def calibration_test_stats(request):
    """
    Get calibration testing statistics
    GET: Returns statistics about calibration tests
    """
    try:
        # Get basic counts
        total_tests = CalibrationTest.objects(is_active=True).count()
        
        # Get overdue calibrations
        overdue_tests = CalibrationTest.objects(
            is_active=True,
            calibration_due_date__lt=datetime.now()
        ).count()
        
        # Get calibrations due in next 30 days
        next_30_days = datetime.now() + timedelta(days=30)
        due_soon_tests = CalibrationTest.objects(
            is_active=True,
            calibration_due_date__lte=next_30_days,
            calibration_due_date__gte=datetime.now()
        ).count()
        
        # Get calibrations done in last 30 days
        last_30_days = datetime.now() - timedelta(days=30)
        recent_calibrations = CalibrationTest.objects(
            is_active=True,
            calibration_date__gte=last_30_days
        ).count()
        
        # Get unique vendors count
        unique_vendors = len(CalibrationTest.objects(is_active=True).distinct('calibration_vendor'))
        
        # Get unique equipment count
        unique_equipment = len(CalibrationTest.objects(is_active=True).distinct('equipment_serial'))
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_tests': total_tests,
                'overdue_tests': overdue_tests,
                'due_soon_tests': due_soon_tests,
                'recent_calibrations': recent_calibrations,
                'unique_vendors': unique_vendors,
                'unique_equipment': unique_equipment,
                'overdue_percentage': round((overdue_tests / total_tests * 100), 2) if total_tests > 0 else 0
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
def calibration_test_overdue(request):
    """
    Get overdue calibration tests
    GET: Returns list of overdue calibration tests with pagination
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get overdue tests
        query = {
            'is_active': True,
            'calibration_due_date__lt': datetime.now()
        }
        
        calibration_tests_queryset = CalibrationTest.objects(**query).order_by('calibration_due_date')
        paginated_tests, total_records = paginate_queryset(calibration_tests_queryset, page, limit)
        
        data = []
        for test in paginated_tests:
            days_overdue = (datetime.now() - test.calibration_due_date).days
            data.append({
                'id': str(test.id),
                'calibration_certification': test.calibration_certification,
                'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                'calibration_vendor': test.calibration_vendor,
                'equipment_name': test.equipment_name,
                'equipment_serial': test.equipment_serial,
                'days_overdue': days_overdue,
                'created_at': safe_datetime_format(test.created_at)
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


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def calibration_test_due_soon(request):
    """
    Get calibration tests due soon (within next 30 days)
    GET: Returns list of calibration tests due soon with pagination
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get tests due soon
        next_30_days = datetime.now() + timedelta(days=30)
        query = {
            'is_active': True,
            'calibration_due_date__lte': next_30_days,
            'calibration_due_date__gte': datetime.now()
        }
        
        calibration_tests_queryset = CalibrationTest.objects(**query).order_by('calibration_due_date')
        paginated_tests, total_records = paginate_queryset(calibration_tests_queryset, page, limit)
        
        data = []
        for test in paginated_tests:
            data.append({
                'id': str(test.id),
                'calibration_certification': test.calibration_certification,
                'calibration_due_date': safe_datetime_format(test.calibration_due_date),
                'calibration_vendor': test.calibration_vendor,
                'equipment_name': test.equipment_name,
                'equipment_serial': test.equipment_serial,
                'days_until_due': test.days_until_due(),
                'created_at': safe_datetime_format(test.created_at)
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