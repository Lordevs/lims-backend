from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from bson import ObjectId
from mongoengine.errors import DoesNotExist, ValidationError

from .models import ProficiencyTest
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


# ============= PROFICIENCY TEST CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def proficiency_test_list(request):
    """
    List all proficiency tests or create a new proficiency test
    GET: Returns list of all proficiency tests with pagination
    POST: Creates a new proficiency test
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get query parameters for filtering
            status_filter = request.GET.get('status', '')
            provider_filter = request.GET.get('provider', '')
            search = request.GET.get('search', '')
            overdue_only = request.GET.get('overdue', '').lower() == 'true'
            
            # Build query
            query = {'is_active': True}
            
            if status_filter:
                query['status'] = status_filter
            
            if provider_filter:
                query['$or'] = [
                    {'provider1': {'$regex': provider_filter, '$options': 'i'}},
                    {'provider2': {'$regex': provider_filter, '$options': 'i'}}
                ]
            
            if search:
                search_query = {
                    '$or': [
                        {'description': {'$regex': search, '$options': 'i'}},
                        {'provider1': {'$regex': search, '$options': 'i'}},
                        {'provider2': {'$regex': search, '$options': 'i'}},
                        {'remarks': {'$regex': search, '$options': 'i'}}
                    ]
                }
                if '$or' in query:
                    # Combine with existing $or query
                    query = {'$and': [query, search_query]}
                else:
                    query.update(search_query)
            
            if overdue_only:
                query['due_date__lt'] = datetime.now()
                query['status__nin'] = ['Completed', 'Cancelled']
            
            # Get proficiency tests with pagination
            proficiency_tests_queryset = ProficiencyTest.objects(**query).order_by('-created_at')
            paginated_tests, total_records = paginate_queryset(proficiency_tests_queryset, page, limit)
            
            data = []
            for test in paginated_tests:
                data.append({
                    'id': str(test.id),
                    'description': test.description,
                    'due_date': safe_datetime_format(test.due_date),
                    'is_active': test.is_active,
                    'last_test_date': safe_datetime_format(test.last_test_date),
                    'next_scheduled_date': safe_datetime_format(test.next_scheduled_date),
                    'provider1': test.provider1,
                    'provider2': test.provider2,
                    'remarks': test.remarks,
                    'status': test.status,
                    'created_at': safe_datetime_format(test.created_at),
                    'updated_at': safe_datetime_format(test.updated_at),
                    'is_overdue': test.is_overdue(),
                    'days_until_due': test.days_until_due()
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
            required_fields = ['description', 'due_date', 'provider1']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Parse datetime fields
            due_date = None
            last_test_date = None
            next_scheduled_date = None
            
            if data.get('due_date'):
                try:
                    due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            if data.get('last_test_date'):
                try:
                    last_test_date = datetime.fromisoformat(data['last_test_date'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid last_test_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            if data.get('next_scheduled_date'):
                try:
                    next_scheduled_date = datetime.fromisoformat(data['next_scheduled_date'].replace('Z', '+00:00'))
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid next_scheduled_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            proficiency_test = ProficiencyTest(
                description=data['description'],
                due_date=due_date,
                is_active=data.get('is_active', True),
                last_test_date=last_test_date,
                next_scheduled_date=next_scheduled_date,
                provider1=data['provider1'],
                provider2=data.get('provider2', ''),
                remarks=data.get('remarks', ''),
                status=data.get('status', 'Scheduled')
            )
            proficiency_test.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Proficiency test created successfully',
                'data': {
                    'id': str(proficiency_test.id),
                    'description': proficiency_test.description,
                    'status': proficiency_test.status,
                    'provider1': proficiency_test.provider1
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
def proficiency_test_detail(request, test_id):
    """
    Get, update, or delete a specific proficiency test by ObjectId
    GET: Returns proficiency test details
    PUT: Updates proficiency test information
    DELETE: Deletes the proficiency test (soft delete)
    """
    try:
        try:
            test = ProficiencyTest.objects.get(id=ObjectId(test_id), is_active=True)
        except (ProficiencyTest.DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Proficiency test not found'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(test.id),
                    'description': test.description,
                    'due_date': safe_datetime_format(test.due_date),
                    'is_active': test.is_active,
                    'last_test_date': safe_datetime_format(test.last_test_date),
                    'next_scheduled_date': safe_datetime_format(test.next_scheduled_date),
                    'provider1': test.provider1,
                    'provider2': test.provider2,
                    'remarks': test.remarks,
                    'status': test.status,
                    'created_at': safe_datetime_format(test.created_at),
                    'updated_at': safe_datetime_format(test.updated_at),
                    'is_overdue': test.is_overdue(),
                    'days_until_due': test.days_until_due()
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
                
                if 'description' in data:
                    update_doc['description'] = data['description']
                
                if 'due_date' in data:
                    try:
                        update_doc['due_date'] = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                    except ValueError:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                        }, status=400)
                
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active']
                
                if 'last_test_date' in data:
                    if data['last_test_date']:
                        try:
                            update_doc['last_test_date'] = datetime.fromisoformat(data['last_test_date'].replace('Z', '+00:00'))
                        except ValueError:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Invalid last_test_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                            }, status=400)
                    else:
                        update_doc['last_test_date'] = None
                
                if 'next_scheduled_date' in data:
                    if data['next_scheduled_date']:
                        try:
                            update_doc['next_scheduled_date'] = datetime.fromisoformat(data['next_scheduled_date'].replace('Z', '+00:00'))
                        except ValueError:
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Invalid next_scheduled_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                            }, status=400)
                    else:
                        update_doc['next_scheduled_date'] = None
                
                if 'provider1' in data:
                    update_doc['provider1'] = data['provider1']
                
                if 'provider2' in data:
                    update_doc['provider2'] = data['provider2']
                
                if 'remarks' in data:
                    update_doc['remarks'] = data['remarks']
                
                if 'status' in data:
                    update_doc['status'] = data['status']
                
                # Apply updates
                if update_doc:
                    test.update(**update_doc)
                    test.reload()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Proficiency test updated successfully',
                    'data': {
                        'id': str(test.id),
                        'description': test.description,
                        'due_date': safe_datetime_format(test.due_date),
                        'is_active': test.is_active,
                        'last_test_date': safe_datetime_format(test.last_test_date),
                        'next_scheduled_date': safe_datetime_format(test.next_scheduled_date),
                        'provider1': test.provider1,
                        'provider2': test.provider2,
                        'remarks': test.remarks,
                        'status': test.status,
                        'updated_at': safe_datetime_format(test.updated_at),
                        'is_overdue': test.is_overdue(),
                        'days_until_due': test.days_until_due()
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
                'message': 'Proficiency test deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def proficiency_test_search(request):
    """
    Search proficiency tests with advanced filtering
    GET: Returns filtered proficiency tests with pagination
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get search parameters
        description = request.GET.get('description', '')
        status = request.GET.get('status', '')
        provider1 = request.GET.get('provider1', '')
        provider2 = request.GET.get('provider2', '')
        due_date_from = request.GET.get('due_date_from', '')
        due_date_to = request.GET.get('due_date_to', '')
        overdue_only = request.GET.get('overdue', '').lower() == 'true'
        
        # Build query
        query = {'is_active': True}
        
        if description:
            query['description__icontains'] = description
        
        if status:
            query['status'] = status
        
        if provider1:
            query['provider1__icontains'] = provider1
        
        if provider2:
            query['provider2__icontains'] = provider2
        
        if due_date_from:
            try:
                from_date = datetime.fromisoformat(due_date_from.replace('Z', '+00:00'))
                query['due_date__gte'] = from_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid due_date_from format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if due_date_to:
            try:
                to_date = datetime.fromisoformat(due_date_to.replace('Z', '+00:00'))
                query['due_date__lte'] = to_date
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid due_date_to format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)
        
        if overdue_only:
            query['due_date__lt'] = datetime.now()
            query['status__nin'] = ['Completed', 'Cancelled']
        
        # Get proficiency tests with pagination
        proficiency_tests_queryset = ProficiencyTest.objects(**query).order_by('-created_at')
        paginated_tests, total_records = paginate_queryset(proficiency_tests_queryset, page, limit)
        
        data = []
        for test in paginated_tests:
            data.append({
                'id': str(test.id),
                'description': test.description,
                'due_date': safe_datetime_format(test.due_date),
                'status': test.status,
                'provider1': test.provider1,
                'provider2': test.provider2,
                'is_overdue': test.is_overdue(),
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


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def proficiency_test_stats(request):
    """
    Get proficiency testing statistics
    GET: Returns statistics about proficiency tests
    """
    try:
        # Get basic counts
        total_tests = ProficiencyTest.objects(is_active=True).count()
        scheduled_tests = ProficiencyTest.objects(is_active=True, status='Scheduled').count()
        in_progress_tests = ProficiencyTest.objects(is_active=True, status='In Progress').count()
        completed_tests = ProficiencyTest.objects(is_active=True, status='Completed').count()
        cancelled_tests = ProficiencyTest.objects(is_active=True, status='Cancelled').count()
        
        # Get overdue tests
        overdue_tests = ProficiencyTest.objects(
            is_active=True,
            due_date__lt=datetime.now(),
            status__nin=['Completed', 'Cancelled']
        ).count()
        
        # Get tests due in next 30 days
        next_30_days = datetime.now() + timedelta(days=30)
        due_soon_tests = ProficiencyTest.objects(
            is_active=True,
            due_date__lte=next_30_days,
            due_date__gte=datetime.now(),
            status__nin=['Completed', 'Cancelled']
        ).count()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_tests': total_tests,
                'scheduled_tests': scheduled_tests,
                'in_progress_tests': in_progress_tests,
                'completed_tests': completed_tests,
                'cancelled_tests': cancelled_tests,
                'overdue_tests': overdue_tests,
                'due_soon_tests': due_soon_tests,
                'completion_rate': round((completed_tests / total_tests * 100), 2) if total_tests > 0 else 0
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
def proficiency_test_overdue(request):    
    """
    Get overdue proficiency tests
    GET: Returns list of overdue proficiency tests with pagination
    """
    try:
        # Get pagination parameters
        page, limit, offset = get_pagination_params(request)
        
        # Get overdue tests
        query = {
            'is_active': True,
            'due_date__lt': datetime.now(),
            'status__nin': ['Completed', 'Cancelled']
        }
        
        proficiency_tests_queryset = ProficiencyTest.objects(**query).order_by('due_date')
        paginated_tests, total_records = paginate_queryset(proficiency_tests_queryset, page, limit)
        
        data = []
        for test in paginated_tests:
            days_overdue = (datetime.now() - test.due_date).days
            data.append({
                'id': str(test.id),
                'description': test.description,
                'due_date': safe_datetime_format(test.due_date),
                'status': test.status,
                'provider1': test.provider1,
                'provider2': test.provider2,
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