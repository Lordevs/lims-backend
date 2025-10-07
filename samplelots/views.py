from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import SampleLot
from samplejobs.models import Job
from testmethods.models import TestMethod
from authentication.decorators import any_authenticated_user


# ============= SAMPLE LOT CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def sample_lot_list(request):
    """
    List all sample lots or create a new sample lot
    GET: Returns list of all sample lots with job and test method information
    POST: Creates a new sample lot
    """
    if request.method == 'GET':
        try:
            # Use raw query to avoid field validation issues
            db = connection.get_db()
            sample_lots_collection = db.sample_lots
            
            # Query to find active sample lots or documents without is_active field (legacy data)
            query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
            sample_lots = sample_lots_collection.find(query)
            data = []
            
            for sample_lot_doc in sample_lots:
                # Get job information
                job_info = {}
                try:
                    job = Job.objects.get(id=ObjectId(sample_lot_doc.get('job_id')))
                    job_info = {
                        'job_id': job.job_id,
                        'project_name': job.project_name,
                        'client_id': str(job.client_id)
                    }
                except (DoesNotExist, Exception):
                    job_info = {'job_id': 'Unknown', 'project_name': 'Unknown', 'client_id': ''}
                
                # Get test methods information (names and count)
                test_method_oids = sample_lot_doc.get('test_method_oids', [])
                test_methods_count = len(test_method_oids) if test_method_oids else 0
                test_method_names = []
                
                # Fetch test method names from test_methods collection
                if test_method_oids:
                    test_methods_collection = db.test_methods
                    for test_method_oid in test_method_oids:
                        try:
                            test_method_doc = test_methods_collection.find_one(
                                {'_id': ObjectId(test_method_oid)}, 
                                {'test_name': 1}
                            )
                            if test_method_doc:
                                test_method_names.append({
                                    'id': str(test_method_doc.get('_id')),
                                    'test_name': test_method_doc.get('test_name', 'Unknown Test')
                                })
                        except Exception:
                            # Skip invalid test method references
                            continue
                
                data.append({
                    'id': str(sample_lot_doc.get('_id', '')),
                    'job_id': str(sample_lot_doc.get('job_id', '')),
                    'job_info': job_info,
                    'item_no': sample_lot_doc.get('item_no', ''),
                    'sample_type': sample_lot_doc.get('sample_type', ''),
                    'material_type': sample_lot_doc.get('material_type', ''),
                    'condition': sample_lot_doc.get('condition', ''),
                    'heat_no': sample_lot_doc.get('heat_no', ''),
                    'description': sample_lot_doc.get('description', ''),
                    'mtc_no': sample_lot_doc.get('mtc_no', ''),
                    'storage_location': sample_lot_doc.get('storage_location', ''),
                    'test_methods_count': test_methods_count,
                    'test_methods': test_method_names,
                    'created_at': sample_lot_doc.get('created_at').isoformat() if sample_lot_doc.get('created_at') else '',
                    'updated_at': sample_lot_doc.get('updated_at').isoformat() if sample_lot_doc.get('updated_at') else ''
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
            required_fields = ['job_id', 'item_no', 'description']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Verify job exists
            try:
                job = Job.objects.get(id=ObjectId(data['job_id']))
            except (DoesNotExist, Exception):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Job not found'
                }, status=404)
            
            # Validate test method IDs if provided
            test_method_oids = []
            if 'test_method_oids' in data and data['test_method_oids']:
                # Use raw MongoDB query to validate test methods (consistent with other operations)
                db = connection.get_db()
                test_methods_collection = db.test_methods
                
                for test_method_id in data['test_method_oids']:
                    try:
                        # Validate ObjectId format
                        test_method_object_id = ObjectId(test_method_id)
                        
                        # Check if test method exists using raw query
                        test_method_doc = test_methods_collection.find_one({
                            '_id': test_method_object_id,
                            '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]
                        })
                        
                        if not test_method_doc:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Test method with ID {test_method_id} not found'
                            }, status=404)
                            
                        test_method_oids.append(test_method_object_id)
                        
                    except Exception:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Invalid test method ID format: {test_method_id}'
                        }, status=400)
            
            sample_lot = SampleLot(
                job_id=ObjectId(data['job_id']),
                item_no=data['item_no'],
                sample_type=data.get('sample_type', ''),
                material_type=data.get('material_type', ''),
                condition=data.get('condition', ''),
                heat_no=data.get('heat_no', ''),
                description=data['description'],
                mtc_no=data.get('mtc_no', ''),
                storage_location=data.get('storage_location', ''),
                test_method_oids=test_method_oids
            )
            sample_lot.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sample lot created successfully',
                'data': {
                    'id': str(sample_lot.id),
                    'item_no': sample_lot.item_no,
                    'job_id': job.job_id,
                    'project_name': job.project_name
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
def sample_lot_detail(request, sample_lot_id):
    """
    Get, update, or delete a specific sample lot by ObjectId
    GET: Returns sample lot details with job and test method information
    PUT: Updates sample lot information (partial update supported)
    DELETE: Deletes the sample lot
    """
    try:
        # Use raw query to find sample lot by item_no
        db = connection.get_db()
        sample_lots_collection = db.sample_lots
        
        # Use raw query to find sample lot by ObjectId (legacy data support)
        try:
            query = {'_id': ObjectId(sample_lot_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
            sample_lot_doc = sample_lots_collection.find_one(query)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid sample lot ID format'
            }, status=400)
        if not sample_lot_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Sample lot not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get job information
            job_info = {}
            try:
                job = Job.objects.get(id=ObjectId(sample_lot_doc.get('job_id')))
                job_info = {
                    'job_id': job.job_id,
                    'project_name': job.project_name,
                    'client_id': str(job.client_id),
                    'end_user': job.end_user,
                    'receive_date': job.receive_date.isoformat()
                }
            except DoesNotExist:
                job_info = {'job_id': 'Unknown', 'project_name': 'Unknown'}
            
            # Get test methods information
            test_methods = []
            test_method_oids = sample_lot_doc.get('test_method_oids', [])
            if test_method_oids:
                test_methods_collection = db.test_methods
                for test_method_oid in test_method_oids:
                    try:
                        test_method_doc = test_methods_collection.find_one(
                            {'_id': ObjectId(test_method_oid)}
                        )
                        if test_method_doc:
                            test_methods.append({
                                'id': str(test_method_doc.get('_id')),
                                'test_name': test_method_doc.get('test_name', 'Unknown Test'),
                                'test_description': test_method_doc.get('test_description', ''),
                                'test_columns': test_method_doc.get('test_columns', []),
                                'hasImage': test_method_doc.get('hasImage', False)
                            })
                    except Exception:
                        # Add placeholder for invalid test method references
                        test_methods.append({
                            'id': str(test_method_oid),
                            'test_name': 'Unknown Test Method',
                            'test_description': 'Test method not found'
                        })
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(sample_lot_doc.get('_id', '')),
                    'job_id': str(sample_lot_doc.get('job_id', '')),
                    'job_info': job_info,
                    'item_no': sample_lot_doc.get('item_no', ''),
                    'sample_type': sample_lot_doc.get('sample_type', ''),
                    'material_type': sample_lot_doc.get('material_type', ''),
                    'condition': sample_lot_doc.get('condition', ''),
                    'heat_no': sample_lot_doc.get('heat_no', ''),
                    'description': sample_lot_doc.get('description', ''),
                    'mtc_no': sample_lot_doc.get('mtc_no', ''),
                    'storage_location': sample_lot_doc.get('storage_location', ''),
                    'test_methods': test_methods,
                    'created_at': sample_lot_doc.get('created_at').isoformat() if sample_lot_doc.get('created_at') else '',
                    'updated_at': sample_lot_doc.get('updated_at').isoformat() if sample_lot_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document (partial update support)
                update_doc = {}
                
                # Update job_id if provided
                if 'job_id' in data:
                    try:
                        job = Job.objects.get(id=ObjectId(data['job_id']))
                        update_doc['job_id'] = ObjectId(data['job_id'])
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Job not found'
                        }, status=404)
                
                # Update test method IDs if provided
                if 'test_method_oids' in data:
                    test_method_oids = []
                    test_methods_collection = db.test_methods
                    
                    for test_method_id in data['test_method_oids']:
                        try:
                            # Validate ObjectId format
                            test_method_object_id = ObjectId(test_method_id)
                            
                            # Check if test method exists using raw query
                            test_method_doc = test_methods_collection.find_one({
                                '_id': test_method_object_id,
                                '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]
                            })
                            
                            if not test_method_doc:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': f'Test method with ID {test_method_id} not found'
                                }, status=404)
                                
                            test_method_oids.append(test_method_object_id)
                            
                        except Exception:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Invalid test method ID format: {test_method_id}'
                            }, status=400)
                    
                    update_doc['test_method_oids'] = test_method_oids
                
                # Update other fields if provided (partial update support)
                updatable_fields = ['item_no', 'sample_type', 'material_type', 'condition', 'heat_no', 
                                   'description', 'mtc_no', 'storage_location']
                for field in updatable_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Only proceed if there are fields to update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No valid fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document (legacy data support)
                update_result = sample_lots_collection.update_one(
                    {'_id': ObjectId(sample_lot_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]},
                    {'$set': update_doc}
                )
                
                if update_result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Sample lot not found or no changes made'
                    }, status=404)
                
                # Get updated sample lot document
                updated_sample_lot = sample_lots_collection.find_one({'_id': ObjectId(sample_lot_id)})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Sample lot updated successfully',
                    'data': {
                        'id': str(updated_sample_lot.get('_id', '')),
                        'item_no': updated_sample_lot.get('item_no', ''),
                        'sample_type': updated_sample_lot.get('sample_type', ''),
                        'updated_at': updated_sample_lot.get('updated_at').isoformat() if updated_sample_lot.get('updated_at') else ''
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
            result = sample_lots_collection.update_one(
                {'_id': ObjectId(sample_lot_id), '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]},
                {'$set': {'is_active': False, 'updated_at': datetime.now()}}
            )
            
            if result.modified_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Sample lot not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sample lot deleted successfully'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def sample_lot_search(request):
    """
    Search sample lots by various criteria
    Query parameters:
    - job_id: Search by job ID (ObjectId)
    - sample_type: Search by sample type
    - material_type: Search by material type
    - item_no: Search by item number (partial match)
    """
    try:
        # Get query parameters
        job_id = request.GET.get('job_id', '')
        sample_type = request.GET.get('sample_type', '')
        material_type = request.GET.get('material_type', '')
        item_no = request.GET.get('item_no', '')
        
        # Build query for raw MongoDB (legacy data support)
        query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
        if job_id:
            try:
                query['job_id'] = ObjectId(job_id)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid job_id format'
                }, status=400)
        if sample_type:
            query['sample_type'] = {'$regex': sample_type, '$options': 'i'}
        if material_type:
            query['material_type'] = {'$regex': material_type, '$options': 'i'}
        if item_no:
            query['item_no'] = {'$regex': item_no, '$options': 'i'}
        
        # Use raw query to search
        db = connection.get_db()
        sample_lots_collection = db.sample_lots
        
        sample_lots = sample_lots_collection.find(query)
        
        data = []
        for sample_lot_doc in sample_lots:
            # Get job information
            job_info = {}
            try:
                job = Job.objects.get(id=ObjectId(sample_lot_doc.get('job_id')))
                job_info = {
                    'job_id': job.job_id,
                    'project_name': job.project_name
                }
            except DoesNotExist:
                job_info = {'job_id': 'Unknown', 'project_name': 'Unknown'}
            
            data.append({
                'id': str(sample_lot_doc.get('_id', '')),
                'job_id': str(sample_lot_doc.get('job_id', '')),
                'job_info': job_info,
                'item_no': sample_lot_doc.get('item_no', ''),
                'sample_type': sample_lot_doc.get('sample_type', ''),
                'material_type': sample_lot_doc.get('material_type', ''),
                'description': sample_lot_doc.get('description', ''),
                'created_at': sample_lot_doc.get('created_at').isoformat() if sample_lot_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'job_id': job_id,
                'sample_type': sample_type,
                'material_type': material_type,
                'item_no': item_no
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
def sample_lot_stats(request):
    """
    Get sample lot statistics
    """
    try:
        # Use raw query to count sample lots (legacy data support)
        db = connection.get_db()
        sample_lots_collection = db.sample_lots
        
        base_query = {'$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
        total_sample_lots = sample_lots_collection.count_documents(base_query)
        
        # Count by sample type (legacy data support)
        sample_type_stats = sample_lots_collection.aggregate([
            {'$match': base_query},
            {'$group': {'_id': '$sample_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by material type (legacy data support)
        material_type_stats = sample_lots_collection.aggregate([
            {'$match': base_query},
            {'$group': {'_id': '$material_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_sample_lots': total_sample_lots,
                'sample_type_distribution': list(sample_type_stats),
                'material_type_distribution': list(material_type_stats)
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
def sample_lot_by_job(request, job_id):
    """
    Get all sample lots for a specific job
    """
    try:
        # Verify job exists
        try:
            job = Job.objects.get(id=ObjectId(job_id))
        except (DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Job not found'
            }, status=404)
        
        # Use raw query to find sample lots by job (legacy data support)
        db = connection.get_db()
        sample_lots_collection = db.sample_lots
        
        query = {'job_id': job.id, '$or': [{'is_active': True}, {'is_active': {'$exists': False}}]}
        sample_lots = sample_lots_collection.find(query)
        
        data = []
        for sample_lot_doc in sample_lots:
            # Get test methods count
            test_methods_count = len(sample_lot_doc.get('test_method_oids', []))
            
            data.append({
                'id': str(sample_lot_doc.get('_id', '')),
                'item_no': sample_lot_doc.get('item_no', ''),
                'sample_type': sample_lot_doc.get('sample_type', ''),
                'material_type': sample_lot_doc.get('material_type', ''),
                'description': sample_lot_doc.get('description', ''),
                'test_methods_count': test_methods_count,
                'created_at': sample_lot_doc.get('created_at').isoformat() if sample_lot_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'job_info': {
                'job_id': job.job_id,
                'project_name': job.project_name,
                'client_id': str(job.client_id)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# @csrf_exempt
# @require_http_methods(["DELETE"])
# def delete_sample_lots_by_job(request, job_id):
#     """
#     Delete all sample lots for a specific job (used for cascading delete)
#     This is called when a job is deleted
#     """
#     try:
#         # Use raw query to soft delete all sample lots for this job
#         db = connection.get_db()
#         sample_lots_collection = db.sample_lots
        
#         result = sample_lots_collection.update_many(
#             {'job_id': ObjectId(job_id), 'is_active': True},
#             {'$set': {'is_active': False, 'updated_at': datetime.now()}}
#         )
        
#         return JsonResponse({
#             'status': 'success',
#             'message': f'Deleted {result.modified_count} sample lots for job {job_id}',
#             'deleted_count': result.modified_count
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         }, status=500)
