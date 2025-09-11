from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from .models import SamplePreparation, SampleLotInfo
from samplelots.models import SampleLot
from samplejobs.models import Job
from testmethods.models import TestMethod
from specimens.models import Specimen


# ============= SAMPLE PREPARATION CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
def sample_preparation_list(request):
    """
    List all sample preparations or create a new sample preparation
    GET: Returns list of all sample preparations with related data
    POST: Creates a new sample preparation with validation
    """
    if request.method == 'GET':
        try:
            # Use raw query to get all sample preparations
            db = connection.get_db()
            sample_preparations_collection = db.sample_preparations
            
            sample_preparations = sample_preparations_collection.find({})
            data = []
            
            for prep_doc in sample_preparations:
                # Process sample_lots array
                sample_lots_data = []
                for sample_lot in prep_doc.get('sample_lots', []):
                    # Get sample lot information with job details
                    sample_lot_info = {
                        'sample_lot_id': str(sample_lot.get('sample_lot_id', '')),
                        'item_no': 'Unknown',
                        'sample_type': 'Unknown',
                        'material_type': 'Unknown',
                        'job_id': 'Unknown'
                    }
                    try:
                        sample_lot_obj = SampleLot.objects.get(id=ObjectId(sample_lot.get('sample_lot_id')))
                        sample_lot_info.update({
                            'item_no': sample_lot_obj.item_no,
                            'sample_type': sample_lot_obj.sample_type,
                            'material_type': sample_lot_obj.material_type
                        })
                        
                        # Get job information from the sample lot's job_id
                        try:
                            job = Job.objects.get(id=ObjectId(sample_lot_obj.job_id))
                            sample_lot_info['job_id'] = job.job_id
                        except (DoesNotExist, Exception):
                            sample_lot_info['job_id'] = 'Unknown'
                            
                    except (DoesNotExist, Exception):
                        sample_lot_info.update({
                            'item_no': 'Unknown',
                            'sample_type': 'Unknown',
                            'material_type': 'Unknown',
                            'job_id': 'Unknown'
                        })
                    
                    # Get test method name
                    test_method_name = 'Unknown Method'
                    try:
                        test_method = TestMethod.objects.get(id=ObjectId(sample_lot.get('test_method_oid')))
                        test_method_name = test_method.test_name
                    except (DoesNotExist, Exception):
                        pass
                    
                    # Get specimens names list
                    specimen_names = []
                    for specimen_oid in sample_lot.get('specimen_oids', []):
                        try:
                            specimen = Specimen.objects.get(id=ObjectId(specimen_oid))
                            specimen_names.append(specimen.specimen_id)
                        except (DoesNotExist, Exception):
                            specimen_names.append('Unknown')
                    
                    sample_lots_data.append({
                        'item_description': sample_lot.get('item_description', ''),
                        'planned_test_date': sample_lot.get('planned_test_date', ''),
                        'dimension_spec': sample_lot.get('dimension_spec', ''),
                        'request_by': sample_lot.get('request_by', ''),
                        'remarks': sample_lot.get('remarks', ''),
                        'job_id': sample_lot_info['job_id'],
                        'item_no': sample_lot_info['item_no'],
                        'test_method_name': test_method_name,
                        'specimens_count': len(specimen_names)
                    })
                
                data.append({
                    'id': str(prep_doc.get('_id', '')),
                    'request_no': prep_doc.get('request_no', ''),
                    'sample_lots': sample_lots_data,
                    'sample_lots_count': len(sample_lots_data),
                    'created_at': prep_doc.get('created_at').isoformat() if prep_doc.get('created_at') else '',
                    'updated_at': prep_doc.get('updated_at').isoformat() if prep_doc.get('updated_at') else ''
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
            required_fields = ['request_no', 'sample_lots']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate sample_lots is an array
            if not isinstance(data['sample_lots'], list) or len(data['sample_lots']) == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'sample_lots must be a non-empty array'
                }, status=400)
            
            # Process and validate each sample lot
            validated_sample_lots = []
            for i, sample_lot_data in enumerate(data['sample_lots']):
                # Validate required fields for each sample lot
                sample_lot_required = ['item_description', 'request_by', 'sample_lot_id', 'test_method_oid', 'specimen_oids']
                for field in sample_lot_required:
                    if field not in sample_lot_data or not sample_lot_data[field]:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Required field "{field}" is missing in sample_lots[{i}]'
                        }, status=400)
                
                # Validate sample lot exists
                try:
                    sample_lot = SampleLot.objects.get(id=ObjectId(sample_lot_data['sample_lot_id']))
                except (DoesNotExist, Exception):
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Sample lot with ID {sample_lot_data["sample_lot_id"]} not found in sample_lots[{i}]'
                    }, status=404)
                
                # Validate test method exists
                try:
                    test_method = TestMethod.objects.get(id=ObjectId(sample_lot_data['test_method_oid']))
                except (DoesNotExist, Exception):
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Test method with ID {sample_lot_data["test_method_oid"]} not found in sample_lots[{i}]'
                    }, status=404)
                
                # Validate specimens exist
                if not isinstance(sample_lot_data['specimen_oids'], list) or len(sample_lot_data['specimen_oids']) == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'specimen_oids must be a non-empty array in sample_lots[{i}]'
                    }, status=400)
                
                validated_specimen_oids = []
                for j, specimen_oid in enumerate(sample_lot_data['specimen_oids']):
                    try:
                        specimen = Specimen.objects.get(id=ObjectId(specimen_oid))
                        validated_specimen_oids.append(ObjectId(specimen_oid))
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Specimen with ID {specimen_oid} not found in sample_lots[{i}].specimen_oids[{j}]'
                        }, status=404)
                
                # Create validated sample lot info
                sample_lot_info = SampleLotInfo(
                    item_description=sample_lot_data['item_description'],
                    planned_test_date=sample_lot_data.get('planned_test_date', ''),
                    dimension_spec=sample_lot_data.get('dimension_spec', ''),
                    request_by=sample_lot_data['request_by'],
                    remarks=sample_lot_data.get('remarks', ''),
                    sample_lot_id=ObjectId(sample_lot_data['sample_lot_id']),
                    test_method_oid=ObjectId(sample_lot_data['test_method_oid']),
                    specimen_oids=validated_specimen_oids
                )
                validated_sample_lots.append(sample_lot_info)
            
            # Create sample preparation
            sample_preparation = SamplePreparation(
                request_no=data['request_no'],
                sample_lots=validated_sample_lots
            )
            sample_preparation.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sample preparation created successfully',
                'data': {
                    'id': str(sample_preparation.id),
                    'request_no': sample_preparation.request_no,
                    'sample_lots_count': len(sample_preparation.sample_lots)
                }
            }, status=201)
            
        except NotUniqueError:
            return JsonResponse({
                'status': 'error',
                'message': f'Sample preparation with request_no "{data.get("request_no", "")}" already exists. Request numbers must be unique.'
            }, status=400)
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
def sample_preparation_detail(request, request_no):
    """
    Get, update, or delete a specific sample preparation by request_no
    GET: Returns sample preparation details with complete relationship data
    PUT: Updates sample preparation
    DELETE: Deletes the sample preparation
    """
    try:
        # Use raw query to find sample preparation by request_no
        db = connection.get_db()
        sample_preparations_collection = db.sample_preparations
        
        prep_doc = sample_preparations_collection.find_one({'request_no': request_no})
        if not prep_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Sample preparation not found'
            }, status=404)
        
        if request.method == 'GET':
            # Process sample_lots array with enhanced relationship data
            sample_lots_data = []
            for sample_lot in prep_doc.get('sample_lots', []):
                # Get detailed sample lot information with job details
                sample_lot_info = {
                    'sample_lot_id': str(sample_lot.get('sample_lot_id', '')),
                    'item_no': 'Unknown',
                    'sample_type': 'Unknown',
                    'material_type': 'Unknown',
                    'job_id': 'Unknown'
                }
                try:
                    sample_lot_obj = SampleLot.objects.get(id=ObjectId(sample_lot.get('sample_lot_id')))
                    sample_lot_info.update({
                        'item_no': sample_lot_obj.item_no,
                        'sample_type': sample_lot_obj.sample_type,
                        'material_type': sample_lot_obj.material_type
                    })
                    
                    # Get job information from the sample lot's job_id
                    try:
                        job = Job.objects.get(id=ObjectId(sample_lot_obj.job_id))
                        sample_lot_info['job_id'] = job.job_id
                    except (DoesNotExist, Exception):
                        sample_lot_info['job_id'] = 'Unknown'
                        
                except (DoesNotExist, Exception):
                    pass
                
                # Get detailed test method information
                test_method_info = {
                    'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                    'new_test_id': 'Unknown',
                    'test_name': 'Unknown Method',
                    'test_description': 'Unknown'
                }
                try:
                    test_method = TestMethod.objects.get(id=ObjectId(sample_lot.get('test_method_oid')))
                    test_method_info.update({
                        'new_test_id': test_method.new_test_id,
                        'test_name': test_method.test_name,
                        'test_description': test_method.test_description,
                        'test_columns': test_method.test_columns,
                        'hasImage': test_method.hasImage,
                        'old_key': test_method.old_key
                    })
                except (DoesNotExist, Exception):
                    pass
                
                # Get detailed specimens information
                specimens_info = []
                specimen_names = []
                for specimen_oid in sample_lot.get('specimen_oids', []):
                    specimen_data = {
                        'id': str(specimen_oid),
                        'specimen_id': 'Unknown'
                    }
                    try:
                        specimen = Specimen.objects.get(id=ObjectId(specimen_oid))
                        specimen_data['specimen_id'] = specimen.specimen_id
                        specimen_names.append(specimen.specimen_id)
                    except (DoesNotExist, Exception):
                        specimen_names.append('Unknown')
                    specimens_info.append(specimen_data)
                
                sample_lots_data.append({
                    'item_description': sample_lot.get('item_description', ''),
                    'planned_test_date': sample_lot.get('planned_test_date', ''),
                    'dimension_spec': sample_lot.get('dimension_spec', ''),
                    'request_by': sample_lot.get('request_by', ''),
                    'remarks': sample_lot.get('remarks', ''),
                    'job_id': sample_lot_info['job_id'],
                    'item_no': sample_lot_info['item_no'],
                    'sample_lot_info': sample_lot_info,
                    'test_method_name': test_method_info['test_name'],
                    'test_method_info': test_method_info,
                    'specimens': specimens_info,
                    'specimens_count': len(specimens_info)
                })
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(prep_doc.get('_id', '')),
                    'request_no': prep_doc.get('request_no', ''),
                    'sample_lots': sample_lots_data,
                    'sample_lots_count': len(sample_lots_data),
                    'total_specimens': sum(len(sl['specimens']) for sl in sample_lots_data),
                    'created_at': prep_doc.get('created_at').isoformat() if prep_doc.get('created_at') else '',
                    'updated_at': prep_doc.get('updated_at').isoformat() if prep_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            # Implementation for updating sample preparation
            try:
                data = json.loads(request.body)
                
                update_doc = {}
                
                # Update request_no if provided
                if 'request_no' in data:
                    new_request_no = data['request_no']
                    if new_request_no != request_no:
                        # Check if new request_no already exists
                        existing_prep = sample_preparations_collection.find_one({'request_no': new_request_no})
                        if existing_prep:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Sample preparation with request_no "{new_request_no}" already exists.'
                            }, status=400)
                        update_doc['request_no'] = new_request_no
                
                # Update sample_lots if provided (simplified - would need full validation like POST)
                if 'sample_lots' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Updating sample_lots is complex. Please use DELETE and CREATE for now.'
                    }, status=400)
                
                update_doc['updated_at'] = datetime.now()
                
                if len(update_doc) <= 1:  # Only timestamp was added
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes provided'
                    }, status=400)
                
                # Update the document
                result = sample_preparations_collection.update_one(
                    {'request_no': request_no},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Sample preparation updated successfully',
                    'data': {
                        'request_no': update_doc.get('request_no', request_no),
                        'updated_at': update_doc['updated_at'].isoformat()
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, status=400)
        
        elif request.method == 'DELETE':
            result = sample_preparations_collection.delete_one({'request_no': request_no})
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Sample preparation not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sample preparation deleted successfully',
                'data': {
                    'request_no': request_no,
                    'deleted_at': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def sample_preparation_search(request):
    """
    Search sample preparations by various criteria
    Query parameters:
    - request_no: Search by request number (partial match)
    - request_by: Search by requester name (partial match)
    """
    try:
        # Get query parameters
        request_no_query = request.GET.get('request_no', '')
        request_by_query = request.GET.get('request_by', '')
        
        # Build query for raw MongoDB
        query = {}
        if request_no_query:
            query['request_no'] = {'$regex': request_no_query, '$options': 'i'}
        if request_by_query:
            query['sample_lots.request_by'] = {'$regex': request_by_query, '$options': 'i'}
        
        # Use raw query to search
        db = connection.get_db()
        sample_preparations_collection = db.sample_preparations
        
        sample_preparations = sample_preparations_collection.find(query)
        
        data = []
        for prep_doc in sample_preparations:
            sample_lots_count = len(prep_doc.get('sample_lots', []))
            total_specimens = sum(len(sl.get('specimen_oids', [])) for sl in prep_doc.get('sample_lots', []))
            
            data.append({
                'id': str(prep_doc.get('_id', '')),
                'request_no': prep_doc.get('request_no', ''),
                'sample_lots_count': sample_lots_count,
                'total_specimens': total_specimens,
                'created_at': prep_doc.get('created_at').isoformat() if prep_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'request_no': request_no_query,
                'request_by': request_by_query
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def sample_preparation_stats(request):
    """
    Get sample preparation statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        sample_preparations_collection = db.sample_preparations
        
        total_preparations = sample_preparations_collection.count_documents({})
        
        # Calculate statistics using aggregation
        pipeline = [
            {
                '$project': {
                    'request_no': 1,
                    'sample_lots_count': {'$size': '$sample_lots'},
                    'total_specimens': {
                        '$sum': {
                            '$map': {
                                'input': '$sample_lots',
                                'as': 'sample_lot',
                                'in': {'$size': '$$sample_lot.specimen_oids'}
                            }
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_sample_lots': {'$sum': '$sample_lots_count'},
                    'total_specimens_used': {'$sum': '$total_specimens'},
                    'avg_sample_lots_per_prep': {'$avg': '$sample_lots_count'},
                    'avg_specimens_per_prep': {'$avg': '$total_specimens'}
                }
            }
        ]
        
        stats_result = list(sample_preparations_collection.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            'total_sample_lots': 0,
            'total_specimens_used': 0,
            'avg_sample_lots_per_prep': 0,
            'avg_specimens_per_prep': 0
        }
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_preparations': total_preparations,
                'total_sample_lots': stats.get('total_sample_lots', 0),
                'total_specimens_used': stats.get('total_specimens_used', 0),
                'avg_sample_lots_per_preparation': round(stats.get('avg_sample_lots_per_prep', 0), 2),
                'avg_specimens_per_preparation': round(stats.get('avg_specimens_per_prep', 0), 2)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
