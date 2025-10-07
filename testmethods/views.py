from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import TestMethod
from authentication.decorators import any_authenticated_user


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


# ============= TEST METHOD CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def test_method_list(request):
    """
    List all test methods or create a new test method
    GET: Returns list of all test methods
    POST: Creates a new test method
    """
    if request.method == 'GET':
        try:
            # Use raw query to get all active test methods
            db = connection.get_db()
            test_methods_collection = db.test_methods
            
            query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
            test_methods = test_methods_collection.find(query)
            data = []
            
            for test_method_doc in test_methods:
                data.append({
                    'id': str(test_method_doc.get('_id', '')),
                    'test_name': test_method_doc.get('test_name', ''),
                    'test_description': test_method_doc.get('test_description', ''),
                    'test_columns': test_method_doc.get('test_columns', []),
                    'hasImage': test_method_doc.get('hasImage', False),
                    'createdAt': safe_datetime_format(test_method_doc.get('createdAt')),
                    'updatedAt': safe_datetime_format(test_method_doc.get('updatedAt'))
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
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['test_name']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            test_method = TestMethod(
                test_name=data['test_name'],
                test_description=data.get('test_description', ''),
                test_columns=data.get('test_columns', []),
                hasImage=data.get('hasImage', False)
            )
            test_method.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Test method created successfully',
                'data': {
                    'id': str(test_method.id),
                    'test_name': test_method.test_name
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
def test_method_detail(request, test_method_id):
    """
    Get, update, or delete a specific test method by ObjectId
    GET: Returns test method details
    PUT: Updates test method information
    DELETE: Deletes the test method
    """
    try:
        # Use raw query to find test method by new_test_id
        db = connection.get_db()
        test_methods_collection = db.test_methods
        
        # Use raw query to find test method by ObjectId (legacy data support)
        try:
            query = {'_id': ObjectId(test_method_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
            test_method_doc = test_methods_collection.find_one(query)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid test method ID format'
            }, status=400)
        if not test_method_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Test method not found'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(test_method_doc.get('_id', '')),
                    'test_name': test_method_doc.get('test_name', ''),
                    'test_description': test_method_doc.get('test_description', ''),
                    'test_columns': test_method_doc.get('test_columns', []),
                    'hasImage': test_method_doc.get('hasImage', False),
                    'createdAt': safe_datetime_format(test_method_doc.get('createdAt')),
                    'updatedAt': safe_datetime_format(test_method_doc.get('updatedAt'))
                }}
            )
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update fields if provided
                update_fields = ['test_name', 'test_description', 'test_columns', 'hasImage']
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Add updated timestamp
                update_doc['updatedAt'] = datetime.now()
                
                # Update the document (legacy data support)
                result = test_methods_collection.update_one(
                    {'_id': ObjectId(test_method_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated test method document
                updated_test_method = test_methods_collection.find_one({'_id': ObjectId(test_method_id)})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Test method updated successfully',
                    'data': {
                        'id': str(updated_test_method.get('_id', '')),
                        'test_name': updated_test_method.get('test_name', ''),
                        'updatedAt': safe_datetime_format(updated_test_method.get('updatedAt'))
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
            # Soft delete by setting is_active to False (legacy data support)
            result = test_methods_collection.update_one(
                {'_id': ObjectId(test_method_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]},
                {'$set': {'is_active': False, 'updatedAt': datetime.now()}}
            )
            
            if result.modified_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Test method not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Test method deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def test_method_search(request):
    """
    Search test methods by various criteria
    Query parameters:
    - test_name: Search by test name (partial match)
    - test_description: Search by test description (partial match)
    - hasImage: Filter by image support (true/false)
    """
    try:
        # Get query parameters
        test_name = request.GET.get('test_name', '')
        test_description = request.GET.get('test_description', '')
        has_image = request.GET.get('hasImage', '')
        
        # Build query for raw MongoDB (legacy data support)
        query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
        if test_name:
            query['test_name'] = {'$regex': test_name, '$options': 'i'}
        if test_description:
            query['test_description'] = {'$regex': test_description, '$options': 'i'}
        if has_image.lower() in ['true', 'false']:
            query['hasImage'] = has_image.lower() == 'true'
        
        # Use raw query to search
        db = connection.get_db()
        test_methods_collection = db.test_methods
        
        test_methods = test_methods_collection.find(query)
        
        data = []
        for test_method_doc in test_methods:
            data.append({
                'id': str(test_method_doc.get('_id', '')),
                'test_name': test_method_doc.get('test_name', ''),
                'test_description': test_method_doc.get('test_description', ''),
                'hasImage': test_method_doc.get('hasImage', False),
                'createdAt': safe_datetime_format(test_method_doc.get('createdAt'))
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'test_name': test_name,
                'test_description': test_description,
                'hasImage': has_image
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
def test_method_stats(request):
    """
    Get test method statistics
    """
    try:
        # Use raw query to count test methods
        db = connection.get_db()
        test_methods_collection = db.test_methods
        
        # Use raw query to count test methods (legacy data support)
        base_query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
        total_test_methods = test_methods_collection.count_documents(base_query)
        
        # Count by hasImage flag (legacy data support)
        image_stats = test_methods_collection.aggregate([
            {'$match': base_query},
            {'$group': {'_id': '$hasImage', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count test methods created by month (legacy data support)
        # Skip monthly stats if createdAt field has inconsistent data types
        try:
            monthly_stats = test_methods_collection.aggregate([
                {'$match': base_query},
                {'$match': {'createdAt': {'$type': 'date'}}},  # Only process actual date objects
                {
                    '$group': {
                        '_id': {
                            'year': {'$year': '$createdAt'},
                            'month': {'$month': '$createdAt'}
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id.year': -1, '_id.month': -1}}
            ])
            monthly_stats_list = list(monthly_stats)
        except Exception:
            # If aggregation fails due to data type issues, return empty stats
            monthly_stats_list = []
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_test_methods': total_test_methods,
                'image_support_distribution': list(image_stats),
                'monthly_creation_stats': monthly_stats_list
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)