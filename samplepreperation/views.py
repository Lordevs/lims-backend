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
from authentication.decorators import any_authenticated_user


# ============= SAMPLE PREPARATION CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
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
                        'job_id': 'Unknown',
                        'client_name': 'Unknown',
                        'project_name': 'Unknown'
                    }
                    
                    # Debug: Check if sample_lot_id exists and is valid
                    sample_lot_id = sample_lot.get('sample_lot_id')
                    if sample_lot_id:
                        try:
                            # Convert to ObjectId if it's a string
                            if isinstance(sample_lot_id, str):
                                sample_lot_id = ObjectId(sample_lot_id)
                            
                            sample_lot_obj = SampleLot.objects.get(id=sample_lot_id)
                            sample_lot_info.update({
                                'item_no': sample_lot_obj.item_no,
                                'sample_type': sample_lot_obj.sample_type,
                                'material_type': sample_lot_obj.material_type
                            })
                            
                            # Get job information from the sample lot's job_id
                            try:
                                if hasattr(sample_lot_obj, 'job_id') and sample_lot_obj.job_id:
                                    job = Job.objects.get(id=sample_lot_obj.job_id)
                                    sample_lot_info['job_id'] = job.job_id
                                    sample_lot_info['project_name'] = job.project_name
                                    
                                    # Get client name from job's client_id
                                    try:
                                        from clients.models import Client
                                        client = Client.objects.get(id=ObjectId(job.client_id))
                                        sample_lot_info['client_name'] = client.client_name
                                    except (DoesNotExist, Exception):
                                        sample_lot_info['client_name'] = 'Unknown Client'
                                else:
                                    sample_lot_info['job_id'] = 'No Job ID'
                            except (DoesNotExist, Exception) as e:
                                sample_lot_info['job_id'] = f'Job Error: {str(e)[:50]}'
                                
                        except (DoesNotExist, Exception) as e:
                            sample_lot_info.update({
                                'item_no': f'Sample Lot Error: {str(e)[:50]}',
                                'sample_type': 'Unknown',
                                'material_type': 'Unknown',
                                'job_id': 'Unknown'
                            })
                    
                    # Get test method information
                    test_method = {
                        'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                        'test_name': 'Unknown Method'
                    }
                    
                    test_method_oid = sample_lot.get('test_method_oid')
                    if test_method_oid:
                        try:
                            # Convert to ObjectId if it's a string
                            if isinstance(test_method_oid, str):
                                test_method_oid = ObjectId(test_method_oid)
                            
                            test_method_obj = TestMethod.objects.get(id=test_method_oid)
                            test_method['test_name'] = test_method_obj.test_name
                        except (DoesNotExist, Exception) as e:
                            test_method['test_name'] = f'Test Method Error: {str(e)[:50]}'
                    
                    # Get specimens information
                    specimens_info = []
                    for specimen_oid in sample_lot.get('specimen_oids', []):
                        specimen_data = {
                            'specimen_oid': str(specimen_oid),
                            'specimen_id': 'Unknown'
                        }
                        try:
                            # Convert to ObjectId if it's a string
                            if isinstance(specimen_oid, str):
                                specimen_oid = ObjectId(specimen_oid)
                            
                            specimen = Specimen.objects.get(id=specimen_oid)
                            specimen_data['specimen_id'] = specimen.specimen_id
                        except (DoesNotExist, Exception) as e:
                            specimen_data['specimen_id'] = f'Specimen Error: {str(e)[:30]}'
                        specimens_info.append(specimen_data)
                    
                    sample_lots_data.append({
                        'planned_test_date': sample_lot.get('planned_test_date'),
                        'dimension_spec': sample_lot.get('dimension_spec'),
                        'request_by': sample_lot.get('request_by'),
                        'remarks': sample_lot.get('remarks'),
                        'sample_lot_id': sample_lot_info['sample_lot_id'],
                        'test_method': test_method,
                        'job_id': sample_lot_info['job_id'],
                        'item_no': sample_lot_info['item_no'],
                        'client_name': sample_lot_info['client_name'],
                        'project_name': sample_lot_info['project_name'],
                        'specimens': specimens_info,
                        'specimens_count': len(specimens_info)
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
            
            # Auto-generate request_no if not provided
            if 'request_no' not in data or not data['request_no']:
                # Generate request_no automatically
                current_year = datetime.now().year
                year_prefix = f"REQ-{current_year}-"
                
                # Find the latest request_no for current year
                db = connection.get_db()
                sample_preparations_collection = db.sample_preparations
                sample_lots_collection = db.sample_lots
                
                # Query for requests from current year, sorted by request_no descending
                latest_request = sample_preparations_collection.find(
                    {'request_no': {'$regex': f'^{year_prefix}', '$options': 'i'}}
                ).sort('request_no', -1).limit(1)
                
                latest_request_list = list(latest_request)
                
                if latest_request_list:
                    # Extract sequence number from latest request
                    latest_request_no = latest_request_list[0]['request_no']
                    try:
                        # Extract the sequence number (last 4 digits)
                        sequence_part = latest_request_no.split('-')[-1]
                        next_sequence = int(sequence_part) + 1
                    except (ValueError, IndexError):
                        # If parsing fails, start from 1
                        next_sequence = 1
                else:
                    # No previous requests for this year, start from 1
                    next_sequence = 1
                
                # Format sequence number with leading zeros (4 digits)
                formatted_sequence = str(next_sequence).zfill(4)
                generated_request_no = f"{year_prefix}{formatted_sequence}"
                
                # Check if generated request_no already exists (safety check)
                existing_check = sample_preparations_collection.find_one({'request_no': generated_request_no})
                if existing_check:
                    # If somehow it exists, increment until we find available one
                    while existing_check:
                        next_sequence += 1
                        formatted_sequence = str(next_sequence).zfill(4)
                        generated_request_no = f"{year_prefix}{formatted_sequence}"
                        existing_check = sample_preparations_collection.find_one({'request_no': generated_request_no})
                
                data['request_no'] = generated_request_no
            
            # Validate required fields (request_no is now auto-generated if not provided)
            required_fields = ['sample_lots']
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
                sample_lot_required = ['sample_lot_id', 'test_method_oid', 'specimen_oids']
                for field in sample_lot_required:
                    if field not in sample_lot_data:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Required field "{field}" is missing in sample_lots[{i}]'
                        }, status=400)
                
                # Validate sample_lot_id (sample lot) exists using raw MongoDB query
                try:
                    sample_lot_id = ObjectId(sample_lot_data['sample_lot_id'])
                    sample_lot_doc = sample_lots_collection.find_one({'_id': sample_lot_id})
                    if not sample_lot_doc:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Sample lot with ID {sample_lot_data["sample_lot_id"]} not found in sample_lots[{i}]'
                        }, status=404)
                except Exception:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Invalid sample lot ID format: {sample_lot_data["sample_lot_id"]} in sample_lots[{i}]'
                    }, status=400)
                
                # Validate test method exists using raw MongoDB query
                try:
                    test_method_id = ObjectId(sample_lot_data['test_method_oid'])
                    test_methods_collection = db.test_methods
                    test_method_doc = test_methods_collection.find_one({'_id': test_method_id})
                    if not test_method_doc:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Test method with ID {sample_lot_data["test_method_oid"]} not found in sample_lots[{i}]'
                        }, status=404)
                except Exception:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Invalid test method ID format: {sample_lot_data["test_method_oid"]} in sample_lots[{i}]'
                    }, status=400)
                
                # Validate specimens exist
                if not isinstance(sample_lot_data['specimen_oids'], list) or len(sample_lot_data['specimen_oids']) == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'specimen_oids must be a non-empty array in sample_lots[{i}]'
                    }, status=400)
                
                validated_specimen_oids = []
                specimens_collection = db.specimens
                for j, specimen_oid in enumerate(sample_lot_data['specimen_oids']):
                    try:
                        specimen_id = ObjectId(specimen_oid)
                        specimen_doc = specimens_collection.find_one({'_id': specimen_id})
                        if not specimen_doc:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Specimen with ID {specimen_oid} not found in sample_lots[{i}].specimen_oids[{j}]'
                            }, status=404)
                        validated_specimen_oids.append(specimen_id)
                    except Exception:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Invalid specimen ID format: {specimen_oid} in sample_lots[{i}].specimen_oids[{j}]'
                        }, status=400)
                
                # Create validated sample lot info
                sample_lot_info = SampleLotInfo(
                    planned_test_date=sample_lot_data.get('planned_test_date'),
                    dimension_spec=sample_lot_data.get('dimension_spec'),
                    request_by=sample_lot_data.get('request_by'),
                    remarks=sample_lot_data.get('remarks'),
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
@any_authenticated_user
def sample_preparation_detail(request, object_id):
    """
    Get, update, or delete a specific sample preparation by ObjectId
    GET: Returns sample preparation details with complete relationship data
    PUT: Partial update of sample preparation
    DELETE: Deletes the sample preparation
    """
    try:
        # Validate ObjectId format
        try:
            obj_id = ObjectId(object_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid ObjectId format'
            }, status=400)
        
        # Use raw query to find sample preparation by ObjectId
        db = connection.get_db()
        sample_preparations_collection = db.sample_preparations
        
        prep_doc = sample_preparations_collection.find_one({'_id': obj_id})
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
                    'job_id': 'Unknown',
                    'client_name': 'Unknown',
                    'project_name': 'Unknown'
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
                        sample_lot_info['project_name'] = job.project_name
                        
                        # Get client name from job's client_id
                        try:
                            from clients.models import Client
                            client = Client.objects.get(id=ObjectId(job.client_id))
                            sample_lot_info['client_name'] = client.client_name
                        except (DoesNotExist, Exception):
                            sample_lot_info['client_name'] = 'Unknown Client'
                            
                    except (DoesNotExist, Exception):
                        sample_lot_info['job_id'] = 'Unknown'
                        
                except (DoesNotExist, Exception):
                    pass
                
                # Get test method information
                test_method = {
                    'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                    'test_name': 'Unknown Method'
                }
                try:
                    # test_method_obj = TestMethod.objects.get(id=ObjectId(sample_lot.get('test_method_oid')))
                    # test_method['test_name'] = test_method_obj.test_name
                    test_methods_collection = db.test_methods
                    test_method_obj = test_methods_collection.find_one({'_id': ObjectId(sample_lot.get('test_method_oid'))})
                    if test_method_obj:
                        test_method.update({
                            'test_name': test_method_obj.get('test_name', 'Unknown Method')
                        })
                except (DoesNotExist, Exception):
                    pass
                
                # Get detailed test method information for detail view
                test_method_info = {
                    'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                    'test_name': 'Unknown Method',
                    'test_description': 'Unknown'
                }
                try:
                    # test_method_obj = TestMethod.objects.get(id=ObjectId(sample_lot.get('test_method_oid')))
                    # test_method_info.update({
                    #     'test_name': test_method_obj.test_name,
                    #     'test_description': test_method_obj.test_description,
                    #     'test_columns': test_method_obj.test_columns,
                    #     'hasImage': test_method_obj.hasImage
                    # })
                    test_methods_collection = db.test_methods
                    test_method_obj = test_methods_collection.find_one({'_id': ObjectId(sample_lot.get('test_method_oid'))})
                    if test_method_obj:
                        test_method_info.update({
                            'test_name': test_method_obj.get('test_name', 'Unknown Method'),
                            'test_description': test_method_obj.get('test_description', 'Unknown'),
                            'test_columns': test_method_obj.get('test_columns', []),
                            'hasImage': test_method_obj.get('hasImage', False)
                        })
                except (DoesNotExist, Exception):
                    pass
                
                # Get detailed specimens information
                specimens_info = []
                for specimen_oid in sample_lot.get('specimen_oids', []):
                    specimen_data = {
                        'specimen_oid': str(specimen_oid),
                        'specimen_id': 'Unknown'
                    }
                    try:
                        specimen = Specimen.objects.get(id=ObjectId(specimen_oid))
                        specimen_data['specimen_id'] = specimen.specimen_id
                    except (DoesNotExist, Exception):
                        pass
                    specimens_info.append(specimen_data)
                
                sample_lots_data.append({
                    'planned_test_date': sample_lot.get('planned_test_date'),
                    'dimension_spec': sample_lot.get('dimension_spec'),
                    'request_by': sample_lot.get('request_by'),
                    'remarks': sample_lot.get('remarks'),
                    'sample_lot_id': sample_lot_info['sample_lot_id'],
                    'test_method': test_method,
                    'job_id': sample_lot_info['job_id'],
                    'item_no': sample_lot_info['item_no'],
                    'client_name': sample_lot_info['client_name'],
                    'project_name': sample_lot_info['project_name'],
                    'sample_lot_info': sample_lot_info,
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
            try:
                data = json.loads(request.body)
                
                # Check if request body is empty
                if not data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Request body cannot be empty'
                    }, status=400)
                
                update_doc = {}
                
                # Update request_no if provided
                if 'request_no' in data:
                    new_request_no = data['request_no']
                    current_request_no = prep_doc.get('request_no')
                    if new_request_no != current_request_no:
                        # Check if new request_no already exists
                        existing_prep = sample_preparations_collection.find_one({
                            'request_no': new_request_no,
                            '_id': {'$ne': obj_id}
                        })
                        if existing_prep:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Sample preparation with request_no "{new_request_no}" already exists.'
                            }, status=400)
                        update_doc['request_no'] = new_request_no
                
                # Update sample_lots if provided (with validation)
                if 'sample_lots' in data:
                    sample_lots_data = data['sample_lots']
                    if not isinstance(sample_lots_data, list):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'sample_lots must be an array'
                        }, status=400)
                    
                    # Validate each sample lot (simplified validation)
                    validated_sample_lots = []
                    for i, sample_lot_data in enumerate(sample_lots_data):
                        # Basic validation
                        required_fields = ['sample_lot_id', 'test_method_oid', 'specimen_oids']
                        for field in required_fields:
                            if field not in sample_lot_data:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': f'Required field "{field}" missing in sample_lots[{i}]'
                                }, status=400)
                        
                        validated_sample_lots.append(sample_lot_data)
                    
                    update_doc['sample_lots'] = validated_sample_lots
                
                update_doc['updated_at'] = datetime.now()
                
                if len(update_doc) <= 1:  # Only timestamp was added
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes provided'
                    }, status=400)
                
                # Update the document
                result = sample_preparations_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated document
                updated_prep = sample_preparations_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Sample preparation updated successfully',
                    'data': {
                        'id': str(updated_prep['_id']),
                        'request_no': updated_prep.get('request_no', ''),
                        'sample_lots_count': len(updated_prep.get('sample_lots', [])),
                        'updated_at': updated_prep['updated_at'].isoformat()
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, status=400)
        
        elif request.method == 'DELETE':
            result = sample_preparations_collection.delete_one({'_id': obj_id})
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Sample preparation not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Sample preparation deleted successfully',
                'data': {
                    'id': str(obj_id),
                    'request_no': prep_doc.get('request_no', ''),
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
@any_authenticated_user
def sample_preparation_search(request):
    """
    Search sample preparations by various criteria
    Query parameters:
    - request_no: Search by request number (partial match)
    - request_by: Search by requester name (partial match)
    - q: Global search across all text fields (request_no, request_by, item_no, sample_type, material_type, job_id, client_name, project_name, test_name, specimen_id)
    """
    try:
        # Get query parameters
        request_no_query = request.GET.get('request_no', '')
        request_by_query = request.GET.get('request_by', '')
        q = request.GET.get('q', '')  # Global search parameter
        
        # Build query for raw MongoDB
        query = {}
        if request_no_query:
            query['request_no'] = {'$regex': request_no_query, '$options': 'i'}
        if request_by_query:
            query['sample_lots.request_by'] = {'$regex': request_by_query, '$options': 'i'}
        
        # Use raw query to search
        db = connection.get_db()
        
        # Handle global search parameter 'q'
        if q:
            # Create OR conditions for global search across multiple fields
            or_conditions = [
                {'request_no': {'$regex': q, '$options': 'i'}},
            ]
            
            # Add cross-collection search for related data
            try:
                # Search in jobs for job_id, project_name
                jobs_collection = db.jobs
                matching_jobs = jobs_collection.find({
                    '$or': [
                        {'job_id': {'$regex': q, '$options': 'i'}},
                        {'project_name': {'$regex': q, '$options': 'i'}}
                    ]
                }, {'_id': 1})
                matching_job_ids = [job['_id'] for job in matching_jobs]
                if matching_job_ids:
                    # Find sample lots for these jobs
                    sample_lots_collection = db.sample_lots
                    sample_lots_for_jobs = sample_lots_collection.find({
                        'job_id': {'$in': matching_job_ids}
                    }, {'_id': 1})
                    job_sample_lot_ids = [lot['_id'] for lot in sample_lots_for_jobs]
                    if job_sample_lot_ids:
                        or_conditions.append({'sample_lots.sample_lot_id': {'$in': job_sample_lot_ids}})
                
                # Search in clients for client_name
                clients_collection = db.clients
                matching_clients = clients_collection.find({
                    '$or': [
                        {'client_name': {'$regex': q, '$options': 'i'}},
                        {'company_name': {'$regex': q, '$options': 'i'}}
                    ]
                }, {'_id': 1})
                matching_client_ids = [client['_id'] for client in matching_clients]
                if matching_client_ids:
                    # Find jobs for these clients
                    jobs_for_clients = jobs_collection.find({
                        'client_id': {'$in': matching_client_ids}
                    }, {'_id': 1})
                    client_job_ids = [job['_id'] for job in jobs_for_clients]
                    if client_job_ids:
                        # Find sample lots for these jobs
                        sample_lots_for_client_jobs = sample_lots_collection.find({
                            'job_id': {'$in': client_job_ids}
                        }, {'_id': 1})
                        client_sample_lot_ids = [lot['_id'] for lot in sample_lots_for_client_jobs]
                        if client_sample_lot_ids:
                            or_conditions.append({'sample_lots.sample_lot_id': {'$in': client_sample_lot_ids}})
                
                # Also add direct client search in sample_lots if they have client_id field
                # This is a fallback in case the relationship chain is different
                try:
                    # Check if sample_lots have direct client_id reference
                    sample_lots_with_clients = sample_lots_collection.find({
                        'client_id': {'$in': matching_client_ids}
                    }, {'_id': 1})
                    direct_client_sample_lot_ids = [lot['_id'] for lot in sample_lots_with_clients]
                    if direct_client_sample_lot_ids:
                        or_conditions.append({'sample_lots.sample_lot_id': {'$in': direct_client_sample_lot_ids}})
                except Exception:
                    pass
                
            except Exception:
                pass
            
            if query:
                # If we have other specific filters, combine them with AND
                query['$and'] = [
                    {k: v for k, v in query.items() if k != '$and'},
                    {'$or': or_conditions}
                ]
            else:
                query['$or'] = or_conditions
        
        sample_preparations_collection = db.sample_preparations
        
        sample_preparations = sample_preparations_collection.find(query)
        
        data = []
        for prep_doc in sample_preparations:
            # Build detailed sample lots data (same as list endpoint)
            sample_lots_data = []
            for sample_lot in prep_doc.get('sample_lots', []):
                # Get sample lot information
                sample_lot_info = {
                    'sample_lot_id': str(sample_lot.get('sample_lot_id', '')),
                    'item_no': 'Unknown',
                    'sample_type': 'Unknown',
                    'material_type': 'Unknown',
                    'job_id': 'Unknown',
                    'client_name': 'Unknown',
                    'project_name': 'Unknown'
                }
                
                # Debug: Check if sample_lot_id exists and is valid
                sample_lot_id = sample_lot.get('sample_lot_id')
                if sample_lot_id:
                    try:
                        # Convert to ObjectId if it's a string
                        if isinstance(sample_lot_id, str):
                            sample_lot_id = ObjectId(sample_lot_id)
                        
                        sample_lot_obj = SampleLot.objects.get(id=sample_lot_id)
                        sample_lot_info.update({
                            'item_no': sample_lot_obj.item_no,
                            'sample_type': sample_lot_obj.sample_type,
                            'material_type': sample_lot_obj.material_type
                        })
                        
                        # Get job information from the sample lot's job_id
                        try:
                            if hasattr(sample_lot_obj, 'job_id') and sample_lot_obj.job_id:
                                job = Job.objects.get(id=sample_lot_obj.job_id)
                                sample_lot_info['job_id'] = job.job_id
                                sample_lot_info['project_name'] = job.project_name
                                
                                # Get client name from job's client_id
                                try:
                                    from clients.models import Client
                                    client = Client.objects.get(id=ObjectId(job.client_id))
                                    sample_lot_info['client_name'] = client.client_name
                                except (DoesNotExist, Exception):
                                    sample_lot_info['client_name'] = 'Unknown Client'
                            else:
                                sample_lot_info['job_id'] = 'No Job ID'
                        except (DoesNotExist, Exception) as e:
                            sample_lot_info['job_id'] = f'Job Error: {str(e)[:50]}'
                            
                    except (DoesNotExist, Exception) as e:
                        sample_lot_info.update({
                            'item_no': f'Sample Lot Error: {str(e)[:50]}',
                            'sample_type': 'Unknown',
                            'material_type': 'Unknown',
                            'job_id': 'Unknown'
                        })
                
                # Get test method information
                test_method = {
                    'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                    'test_name': 'Unknown Method'
                }
                
                test_method_oid = sample_lot.get('test_method_oid')
                if test_method_oid:
                    try:
                        # Convert to ObjectId if it's a string
                        if isinstance(test_method_oid, str):
                            test_method_oid = ObjectId(test_method_oid)
                        
                        test_method_obj = TestMethod.objects.get(id=test_method_oid)
                        test_method['test_name'] = test_method_obj.test_name
                    except (DoesNotExist, Exception) as e:
                        test_method['test_name'] = f'Test Method Error: {str(e)[:50]}'
                
                # Get specimens information
                specimens_info = []
                for specimen_oid in sample_lot.get('specimen_oids', []):
                    specimen_data = {
                        'specimen_oid': str(specimen_oid),
                        'specimen_id': 'Unknown'
                    }
                    try:
                        # Convert to ObjectId if it's a string
                        if isinstance(specimen_oid, str):
                            specimen_oid = ObjectId(specimen_oid)
                        
                        specimen = Specimen.objects.get(id=specimen_oid)
                        specimen_data['specimen_id'] = specimen.specimen_id
                    except (DoesNotExist, Exception) as e:
                        specimen_data['specimen_id'] = f'Specimen Error: {str(e)[:30]}'
                    specimens_info.append(specimen_data)
                
                sample_lots_data.append({
                    'planned_test_date': sample_lot.get('planned_test_date'),
                    'dimension_spec': sample_lot.get('dimension_spec'),
                    'request_by': sample_lot.get('request_by'),
                    'remarks': sample_lot.get('remarks'),
                    'sample_lot_id': sample_lot_info['sample_lot_id'],
                    'test_method': test_method,
                    'job_id': sample_lot_info['job_id'],
                    'item_no': sample_lot_info['item_no'],
                    'client_name': sample_lot_info['client_name'],
                    'project_name': sample_lot_info['project_name'],
                    'specimens': specimens_info,
                    'specimens_count': len(specimens_info)
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
            'total': len(data),
            'filters_applied': {
                'request_no': request_no_query,
                'request_by': request_by_query,
                'q': q
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


@csrf_exempt
@require_http_methods(["GET"])
def sample_preparation_by_job(request, job_oid):
    """
    Get all sample preparations for a specific job by ObjectId
    """
    try:
        # Validate ObjectId format
        try:
            job_obj_id = ObjectId(job_oid)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid job ID format: {job_oid}'
            }, status=400)
        
        # Use raw query to find sample preparations for this job
        db = connection.get_db()
        sample_preparations_collection = db.sample_preparations
        
        # Find the job first to validate it exists
        jobs_collection = db.jobs
        job_doc = jobs_collection.find_one({'_id': job_obj_id})
        if not job_doc:
            return JsonResponse({
                'status': 'error',
                'message': f'Job with ID {job_oid} not found'
            }, status=404)
        
        # Get client information for the job
        client_name = 'Unknown'
        try:
            clients_collection = db.clients
            client_obj_id = job_doc.get('client_id')
            if client_obj_id:
                if isinstance(client_obj_id, str):
                    client_obj_id = ObjectId(client_obj_id)
                client_doc = clients_collection.find_one({'_id': client_obj_id})
                if client_doc:
                    client_name = client_doc.get('client_name', 'Unknown')
        except Exception:
            pass
        
        # Get all sample preparations
        sample_preparations = sample_preparations_collection.find({}).sort('created_at', -1)
        data = []
        
        for prep_doc in sample_preparations:
            # Check if this sample preparation has any sample lots from the specified job
            has_job_sample_lots = False
            sample_lots_data = []
            
            for sample_lot in prep_doc.get('sample_lots', []):
                # Get sample lot information
                sample_lot_id = sample_lot.get('sample_lot_id')
                if sample_lot_id:
                    try:
                        sample_lots_collection = db.sample_lots
                        sample_lot_doc = sample_lots_collection.find_one({'_id': ObjectId(sample_lot_id)})
                        
                        if sample_lot_doc and sample_lot_doc.get('job_id') == job_obj_id:
                            has_job_sample_lots = True
                            
                            # Get job information
                            job_info = {
                                'job_id': job_doc.get('job_id', 'Unknown'),
                                'project_name': job_doc.get('project_name', ''),
                                'end_user': job_doc.get('end_user', ''),
                                'receive_date': job_doc.get('receive_date', ''),
                                'received_by': job_doc.get('received_by', ''),
                                'remarks': job_doc.get('remarks', '')
                            }
                            
                            # Get client information
                            client_name = 'Unknown'
                            try:
                                clients_collection = db.clients
                                client_obj_id = job_doc.get('client_id')
                                if client_obj_id:
                                    if isinstance(client_obj_id, str):
                                        client_obj_id = ObjectId(client_obj_id)
                                    client_doc = clients_collection.find_one({'_id': client_obj_id})
                                    if client_doc:
                                        client_name = client_doc.get('client_name', 'Unknown')
                            except Exception:
                                pass
                            
                            # Get test method information
                            test_method_info = {
                                'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                                'test_name': 'Unknown Method',
                                'test_description': 'Unknown'
                            }
                            try:
                                test_methods_collection = db.test_methods
                                test_method_doc = test_methods_collection.find_one({'_id': ObjectId(sample_lot.get('test_method_oid'))})
                                if test_method_doc:
                                    test_method_info.update({
                                        'test_name': test_method_doc.get('test_name', 'Unknown Method'),
                                        'test_description': test_method_doc.get('test_description', 'Unknown'),
                                        'test_columns': test_method_doc.get('test_columns', []),
                                        'hasImage': test_method_doc.get('hasImage', False)
                                    })
                            except Exception:
                                pass
                            
                            # Get specimens information for this sample lot
                            sample_lot_specimens = []
                            for specimen_oid in sample_lot.get('specimen_oids', []):
                                specimen_info = {
                                    'specimen_oid': str(specimen_oid),
                                    'specimen_id': 'Unknown',
                                    'created_at': '',
                                    'updated_at': ''
                                }
                                try:
                                    specimens_collection = db.specimens
                                    specimen_doc = specimens_collection.find_one({'_id': ObjectId(specimen_oid)})
                                    if specimen_doc:
                                        specimen_info.update({
                                            'specimen_id': specimen_doc.get('specimen_id', 'Unknown'),
                                            'created_at': specimen_doc.get('created_at').isoformat() if specimen_doc.get('created_at') else '',
                                            'updated_at': specimen_doc.get('updated_at').isoformat() if specimen_doc.get('updated_at') else ''
                                        })
                                except Exception:
                                    pass
                                
                                sample_lot_specimens.append(specimen_info)
                            
                            sample_lots_data.append({
                                'planned_test_date': sample_lot.get('planned_test_date'),
                                'dimension_spec': sample_lot.get('dimension_spec'),
                                'request_by': sample_lot.get('request_by'),
                                'remarks': sample_lot.get('remarks'),
                                'sample_lot_info': {
                                    'sample_lot_id': str(sample_lot_id),
                                    'item_no': sample_lot_doc.get('item_no', 'Unknown'),
                                    'sample_type': sample_lot_doc.get('sample_type', 'Unknown'),
                                    'material_type': sample_lot_doc.get('material_type', 'Unknown'),
                                    'description': sample_lot_doc.get('description', 'Unknown'),
                                    'job_id': job_info['job_id'],
                                    'client_name': client_name
                                },
                                'test_method': test_method_info,
                                'specimens': sample_lot_specimens,
                                'specimens_count': len(sample_lot_specimens)
                            })
                    except Exception:
                        pass
            
            # Only include this sample preparation if it has sample lots from the specified job
            if has_job_sample_lots:
                data.append({
                    'id': str(prep_doc.get('_id', '')),
                    'request_no': prep_doc.get('request_no', ''),
                    'sample_lots': sample_lots_data,
                    'sample_lots_count': len(sample_lots_data),
                    'total_specimens': sum(len(lot.get('specimens', [])) for lot in sample_lots_data),
                    'created_at': prep_doc.get('created_at').isoformat() if prep_doc.get('created_at') else '',
                    'updated_at': prep_doc.get('updated_at').isoformat() if prep_doc.get('updated_at') else ''
                })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'job_oid': job_oid,
            'job_id': job_doc.get('job_id', ''),
            'project_name': job_doc.get('project_name', ''),
            'client_name': client_name
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
