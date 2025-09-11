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


# ============= TEST METHOD CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
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
            
            test_methods = test_methods_collection.find({'is_active': True})
            data = []
            
            for test_method_doc in test_methods:
                data.append({
                    'id': str(test_method_doc.get('_id', '')),
                    'new_test_id': test_method_doc.get('new_test_id'),
                    'test_name': test_method_doc.get('test_name', ''),
                    'test_description': test_method_doc.get('test_description', ''),
                    'test_columns': test_method_doc.get('test_columns', []),
                    'hasImage': test_method_doc.get('hasImage', False),
                    'old_key': test_method_doc.get('old_key', ''),
                    'createdAt': test_method_doc.get('createdAt').isoformat() if test_method_doc.get('createdAt') else '',
                    'updatedAt': test_method_doc.get('updatedAt').isoformat() if test_method_doc.get('updatedAt') else ''
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
            required_fields = ['new_test_id', 'test_name']
            for field in required_fields:
                if field not in data or data[field] is None:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            test_method = TestMethod(
                new_test_id=data['new_test_id'],
                test_name=data['test_name'],
                test_description=data.get('test_description', ''),
                test_columns=data.get('test_columns', []),
                hasImage=data.get('hasImage', False),
                old_key=data.get('old_key', '')
            )
            test_method.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Test method created successfully',
                'data': {
                    'id': str(test_method.id),
                    'new_test_id': test_method.new_test_id,
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
def test_method_detail(request, new_test_id):
    """
    Get, update, or delete a specific test method by new_test_id
    GET: Returns test method details
    PUT: Updates test method information
    DELETE: Deletes the test method
    """
    try:
        # Use raw query to find test method by new_test_id
        db = connection.get_db()
        test_methods_collection = db.test_methods
        
        test_method_doc = test_methods_collection.find_one({'new_test_id': int(new_test_id), 'is_active': True})
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
                    'new_test_id': test_method_doc.get('new_test_id'),
                    'test_name': test_method_doc.get('test_name', ''),
                    'test_description': test_method_doc.get('test_description', ''),
                    'test_columns': test_method_doc.get('test_columns', []),
                    'hasImage': test_method_doc.get('hasImage', False),
                    'old_key': test_method_doc.get('old_key', ''),
                    'createdAt': test_method_doc.get('createdAt').isoformat() if test_method_doc.get('createdAt') else '',
                    'updatedAt': test_method_doc.get('updatedAt').isoformat() if test_method_doc.get('updatedAt') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update fields if provided
                update_fields = ['test_name', 'test_description', 'test_columns', 'hasImage', 'old_key']
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Add updated timestamp
                update_doc['updatedAt'] = datetime.now()
                
                # Update the document
                result = test_methods_collection.update_one(
                    {'new_test_id': int(new_test_id), 'is_active': True},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated test method document
                updated_test_method = test_methods_collection.find_one({'new_test_id': int(new_test_id)})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Test method updated successfully',
                    'data': {
                        'id': str(updated_test_method.get('_id', '')),
                        'new_test_id': updated_test_method.get('new_test_id'),
                        'test_name': updated_test_method.get('test_name', ''),
                        'updatedAt': updated_test_method.get('updatedAt').isoformat() if updated_test_method.get('updatedAt') else ''
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
            result = test_methods_collection.update_one(
                {'new_test_id': int(new_test_id), 'is_active': True},
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
        
        # Build query for raw MongoDB
        query = {'is_active': True}
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
                'new_test_id': test_method_doc.get('new_test_id'),
                'test_name': test_method_doc.get('test_name', ''),
                'test_description': test_method_doc.get('test_description', ''),
                'hasImage': test_method_doc.get('hasImage', False),
                'createdAt': test_method_doc.get('createdAt').isoformat() if test_method_doc.get('createdAt') else ''
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
def test_method_stats(request):
    """
    Get test method statistics
    """
    try:
        # Use raw query to count test methods
        db = connection.get_db()
        test_methods_collection = db.test_methods
        
        total_test_methods = test_methods_collection.count_documents({'is_active': True})
        
        # Count by hasImage flag
        image_stats = test_methods_collection.aggregate([
            {'$match': {'is_active': True}},
            {'$group': {'_id': '$hasImage', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count test methods created by month
        monthly_stats = test_methods_collection.aggregate([
            {'$match': {'is_active': True}},
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
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_test_methods': total_test_methods,
                'image_support_distribution': list(image_stats),
                'monthly_creation_stats': list(monthly_stats)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)