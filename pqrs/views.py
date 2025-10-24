from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import PQR
from welders.models import Welder
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def pqr_list(request):
    """
    List all PQRs or create a new PQR
    GET: Returns list of all PQRs with welder information
    POST: Creates a new PQR
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get search parameters
            law_name_search = request.GET.get('law_name', '')
            lab_test_no_search = request.GET.get('lab_test_no', '')
            type_search = request.GET.get('type', '')
            
            # Get filtering parameters
            show_inactive = request.GET.get('show_inactive', '').lower() == 'true'
            include_inactive = request.GET.get('include_inactive', '').lower() == 'true'
            
            # Use raw query to get all active PQRs
            db = connection.get_db()
            pqrs_collection = db.pqrs
            
            # Build query based on search parameters
            query = {}
            if law_name_search:
                query['law_name'] = {'$regex': law_name_search, '$options': 'i'}
            if lab_test_no_search:
                query['lab_test_no'] = {'$regex': lab_test_no_search, '$options': 'i'}
            if type_search:
                query['type'] = {'$regex': type_search, '$options': 'i'}
            
            # Add filtering based on is_active status
            if show_inactive:
                # Only show inactive PQRs
                query['is_active'] = False
            elif include_inactive:
                # Show both active and inactive PQRs (no filter)
                pass
            else:
                # Default: only show active PQRs
                query['is_active'] = True
            
            # Get total count for pagination
            total_records = pqrs_collection.count_documents(query)
            
            # Get paginated PQRs
            pqrs = pqrs_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for pqr_doc in pqrs:
                # Get welder information
                welder_info = {
                    'welder_id': '',
                    'operator_name': 'Unknown Welder',
                    'operator_id': '',
                    'iqama': '',
                    'profile_image': None
                }
                
                try:
                    # Get welder information directly
                    welder_obj_id = pqr_doc.get('welder_id')
                    if welder_obj_id:
                        if isinstance(welder_obj_id, str):
                            welder_obj_id = ObjectId(welder_obj_id)
                        welders_collection = db.welders
                        welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                        if welder_doc:
                            welder_info = {
                                'welder_id': str(welder_doc.get('_id', '')),
                                'operator_name': welder_doc.get('operator_name', 'Unknown Welder'),
                                'operator_id': welder_doc.get('operator_id', ''),
                                'iqama': welder_doc.get('iqama', ''),
                                'profile_image': welder_doc.get('profile_image', ''),
                                'profile_image_url': f"/media/{welder_doc.get('profile_image', '')}" if welder_doc.get('profile_image', '') else None
                            }
                except Exception:
                    pass
                
                data.append({
                    'id': str(pqr_doc.get('_id', '')),
                    'type': pqr_doc.get('type', ''),
                    'basic_info': pqr_doc.get('basic_info', {}),
                    'joints': pqr_doc.get('joints', {}),
                    'joint_design_sketch': pqr_doc.get('joint_design_sketch', []),
                    'base_metals': pqr_doc.get('base_metals', {}),
                    'filler_metals': pqr_doc.get('filler_metals', {}),
                    'positions': pqr_doc.get('positions', {}),
                    'preheat': pqr_doc.get('preheat', {}),
                    'post_weld_heat_treatment': pqr_doc.get('post_weld_heat_treatment', {}),
                    'gas': pqr_doc.get('gas', {}),
                    'electrical_characteristics': pqr_doc.get('electrical_characteristics', {}),
                    'techniques': pqr_doc.get('techniques', {}),
                    'welding_parameters': pqr_doc.get('welding_parameters', {}),
                    'tensile_test': pqr_doc.get('tensile_test', {}),
                    'guided_bend_test': pqr_doc.get('guided_bend_test', {}),
                    'toughness_test': pqr_doc.get('toughness_test', {}),
                    'fillet_weld_test': pqr_doc.get('fillet_weld_test', {}),
                    'other_tests': pqr_doc.get('other_tests', {}),
                    'welder_id': str(pqr_doc.get('welder_id', '')),
                    'welder_info': welder_info,
                    'mechanical_testing_conducted_by': pqr_doc.get('mechanical_testing_conducted_by', ''),
                    'lab_test_no': pqr_doc.get('lab_test_no', ''),
                    'law_name': pqr_doc.get('law_name', ''),
                    'signatures': pqr_doc.get('signatures', {}),
                    'is_active': pqr_doc.get('is_active', True),
                    'created_at': pqr_doc.get('created_at').isoformat() if pqr_doc.get('created_at') else '',
                    'updated_at': pqr_doc.get('updated_at').isoformat() if pqr_doc.get('updated_at') else ''
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
            # Extract form data
            data = request.POST.dict()
            
            # Validate required fields
            required_fields = ['type', 'welder_id', 'mechanical_testing_conducted_by', 'lab_test_no', 'law_name']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate that the welder exists
            try:
                welder = Welder.objects.get(id=ObjectId(data['welder_id']))
            except (DoesNotExist, Exception) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Welder not found: {str(e)}'
                }, status=400)
            
            # Helper function to parse JSON strings from form data
            def parse_json_field(field_value):
                if not field_value:
                    return {}
                try:
                    return json.loads(field_value)
                except (json.JSONDecodeError, TypeError):
                    return {}
            
            # Parse boolean field
            is_active = data.get('is_active', 'true').lower() in ['true', '1', 'yes']
            
            # Create PQR first without images to get the PQR ID
            pqr = PQR(
                type=data['type'],
                basic_info=parse_json_field(data.get('basic_info')),
                joints=parse_json_field(data.get('joints')),
                joint_design_sketch=[],  # Will be updated after upload
                base_metals=parse_json_field(data.get('base_metals')),
                filler_metals=parse_json_field(data.get('filler_metals')),
                positions=parse_json_field(data.get('positions')),
                preheat=parse_json_field(data.get('preheat')),
                post_weld_heat_treatment=parse_json_field(data.get('post_weld_heat_treatment')),
                gas=parse_json_field(data.get('gas')),
                electrical_characteristics=parse_json_field(data.get('electrical_characteristics')),
                techniques=parse_json_field(data.get('techniques')),
                welding_parameters=parse_json_field(data.get('welding_parameters')),
                tensile_test=parse_json_field(data.get('tensile_test')),
                guided_bend_test=parse_json_field(data.get('guided_bend_test')),
                toughness_test=parse_json_field(data.get('toughness_test')),
                fillet_weld_test=parse_json_field(data.get('fillet_weld_test')),
                other_tests=parse_json_field(data.get('other_tests')),
                welder_id=ObjectId(data['welder_id']),
                mechanical_testing_conducted_by=data['mechanical_testing_conducted_by'],
                lab_test_no=data['lab_test_no'],
                law_name=data['law_name'],
                signatures=parse_json_field(data.get('signatures')),
                is_active=is_active
            )
            pqr.save()
            
            # Now handle joint_design_sketch file uploads with PQR ID
            joint_design_sketch = []
            if 'joint_design_sketch' in request.FILES:
                import uuid
                import os
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                from django.conf import settings
                
                pqr_id = str(pqr.id)
                uploaded_files = request.FILES.getlist('joint_design_sketch')
                
                for uploaded_file in uploaded_files:
                    if uploaded_file and uploaded_file.size > 0:
                        # Get file extension
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        
                        # Generate unique filename with timestamp
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        unique_filename = f"joint_sketch_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
                        
                        # Create directory path using PQR ID
                        directory_path = f"pqrs/{pqr_id}/"
                        
                        # Read file content
                        uploaded_file.seek(0)
                        file_content = uploaded_file.read()
                        
                        # Save file
                        file_path = default_storage.save(
                            f"{directory_path}{unique_filename}",
                            ContentFile(file_content)
                        )
                        
                        # Store the file path
                        joint_design_sketch.append(file_path)
                
                # Update PQR with image paths
                if joint_design_sketch:
                    pqr.joint_design_sketch = joint_design_sketch
                    pqr.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'PQR created successfully',
                'data': {
                    'id': str(pqr.id),
                    'type': pqr.type,
                    'lab_test_no': pqr.lab_test_no,
                    'law_name': pqr.law_name,
                    'joint_design_sketch': [f"{settings.MEDIA_URL}{file}" for file in joint_design_sketch]
                }
            }, status=201)
            
        except ValidationError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Validation error: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@any_authenticated_user
def pqr_detail(request, object_id):
    """
    Get, update, or delete a specific PQR by ObjectId
    GET: Returns PQR details with welder information
    PUT: Updates PQR information
    DELETE: Deletes the PQR
    """
    try:
        # Validate ObjectId format
        try:
            obj_id = ObjectId(object_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid PQR ID format: {object_id}'
            }, status=400)
        
        # Use raw query to find PQR by ObjectId
        db = connection.get_db()
        pqrs_collection = db.pqrs
        
        pqr_doc = pqrs_collection.find_one({'_id': obj_id})
        if not pqr_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'PQR not found'
            }, status=404)
        
        if request.method == 'GET':
            from django.conf import settings
            
            # Get welder information
            welder_info = {
                'welder_id': '',
                'operator_name': 'Unknown Welder',
                'operator_id': '',
                'iqama': '',
                'profile_image': None,
                'profile_image_url': None
            }
            
            try:
                # Get welder information directly
                welder_obj_id = pqr_doc.get('welder_id')
                if welder_obj_id:
                    if isinstance(welder_obj_id, str):
                        welder_obj_id = ObjectId(welder_obj_id)
                    welders_collection = db.welders
                    welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                    if welder_doc:
                        welder_info = {
                            'welder_id': str(welder_doc.get('_id', '')),
                            'operator_name': welder_doc.get('operator_name', 'Unknown Welder'),
                            'operator_id': welder_doc.get('operator_id', ''),
                            'iqama': welder_doc.get('iqama', ''),
                            'profile_image': welder_doc.get('profile_image', ''),
                            'profile_image_url': f"{settings.MEDIA_URL}{welder_doc.get('profile_image', '')}" if welder_doc.get('profile_image', '') else None
                        }
            except Exception:
                pass
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(pqr_doc.get('_id', '')),
                    'type': pqr_doc.get('type', ''),
                    'basic_info': pqr_doc.get('basic_info', {}),
                    'joints': pqr_doc.get('joints', {}),
                    'joint_design_sketch': [f"{settings.MEDIA_URL}{file}" for file in pqr_doc.get('joint_design_sketch', [])],
                    'base_metals': pqr_doc.get('base_metals', {}),
                    'filler_metals': pqr_doc.get('filler_metals', {}),
                    'positions': pqr_doc.get('positions', {}),
                    'preheat': pqr_doc.get('preheat', {}),
                    'post_weld_heat_treatment': pqr_doc.get('post_weld_heat_treatment', {}),
                    'gas': pqr_doc.get('gas', {}),
                    'electrical_characteristics': pqr_doc.get('electrical_characteristics', {}),
                    'techniques': pqr_doc.get('techniques', {}),
                    'welding_parameters': pqr_doc.get('welding_parameters', {}),
                    'tensile_test': pqr_doc.get('tensile_test', {}),
                    'guided_bend_test': pqr_doc.get('guided_bend_test', {}),
                    'toughness_test': pqr_doc.get('toughness_test', {}),
                    'fillet_weld_test': pqr_doc.get('fillet_weld_test', {}),
                    'other_tests': pqr_doc.get('other_tests', {}),
                    'welder_id': str(pqr_doc.get('welder_id', '')),
                    'welder_info': welder_info,
                    'mechanical_testing_conducted_by': pqr_doc.get('mechanical_testing_conducted_by', ''),
                    'lab_test_no': pqr_doc.get('lab_test_no', ''),
                    'law_name': pqr_doc.get('law_name', ''),
                    'signatures': pqr_doc.get('signatures', {}),
                    'is_active': pqr_doc.get('is_active', True),
                    'created_at': pqr_doc.get('created_at').isoformat() if pqr_doc.get('created_at') else '',
                    'updated_at': pqr_doc.get('updated_at').isoformat() if pqr_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            from django.conf import settings
            
            try:
                # Debug: Check request content type and data
                print(f"Content-Type: {request.content_type}")
                print(f"POST data: {request.POST}")
                print(f"FILES data: {request.FILES}")
                
                # Extract form data - handle both form data and JSON
                if request.content_type and 'application/json' in request.content_type:
                    # Handle JSON data
                    try:
                        data = json.loads(request.body)
                        print(f"JSON data: {data}")
                    except json.JSONDecodeError:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid JSON format'
                        }, status=400)
                elif request.content_type and 'multipart/form-data' in request.content_type:
                    # Handle multipart form data for PUT requests
                    try:
                        from django.http.multipartparser import MultiPartParser
                        from django.core.files.uploadhandler import MemoryFileUploadHandler
                        from io import BytesIO
                        
                        # Create upload handlers
                        upload_handlers = [MemoryFileUploadHandler()]
                        
                        # Create a file-like object from the request body
                        body_file = BytesIO(request.body)
                        
                        # Parse the multipart data
                        parser = MultiPartParser(request.META, body_file, upload_handlers)
                        parsed_data, files = parser.parse()
                        
                        # Convert QueryDict to regular dict for easier handling
                        data = {}
                        for key, value in parsed_data.items():
                            if isinstance(value, list) and len(value) == 1:
                                data[key] = value[0]
                            else:
                                data[key] = value
                        
                        print(f"Parsed multipart data: {data}")
                        print(f"Parsed files: {files}")
                        
                    except Exception as e:
                        print(f"Error parsing multipart data: {e}")
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Failed to parse multipart form data: {str(e)}'
                        }, status=400)
                else:
                    # Handle regular form data
                    data = request.POST.dict()
                    print(f"Form data: {data}")
                
                # Prepare update document
                update_doc = {}
                
                # Update welder_id if provided
                if 'welder_id' in data:
                    try:
                        welder = Welder.objects.get(id=ObjectId(data['welder_id']))
                        update_doc['welder_id'] = ObjectId(data['welder_id'])
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Welder not found'
                        }, status=404)
                
                # Helper function to parse JSON strings from form data
                def parse_json_field(field_value):
                    if not field_value:
                        return {}
                    try:
                        return json.loads(field_value)
                    except (json.JSONDecodeError, TypeError):
                        return {}
                
                # Handle joint_design_sketch file uploads
                files_to_process = files if 'files' in locals() else request.FILES
                if 'joint_design_sketch' in files_to_process:
                    import uuid
                    import os
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    from django.conf import settings
                    
                    joint_design_sketch = []
                    pqr_id = str(obj_id)
                    uploaded_files = files_to_process.getlist('joint_design_sketch')
                    
                    for uploaded_file in uploaded_files:
                        if uploaded_file and uploaded_file.size > 0:
                            # Get file extension
                            file_extension = os.path.splitext(uploaded_file.name)[1]
                            
                            # Generate unique filename with timestamp
                            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                            unique_filename = f"joint_sketch_{timestamp}_{uuid.uuid4().hex[:8]}{file_extension}"
                            
                            # Create directory path using PQR ID
                            directory_path = f"pqrs/{pqr_id}/"
                            
                            # Read file content
                            uploaded_file.seek(0)
                            file_content = uploaded_file.read()
                            
                            # Save file
                            file_path = default_storage.save(
                                f"{directory_path}{unique_filename}",
                                ContentFile(file_content)
                            )
                            
                            # Store the file path
                            joint_design_sketch.append(file_path)
                    
                    # If files were uploaded, update the field
                    if joint_design_sketch:
                        update_doc['joint_design_sketch'] = joint_design_sketch
                
                # Update other fields if provided
                update_fields = [
                    'type', 'mechanical_testing_conducted_by', 'lab_test_no', 'law_name'
                ]
                
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Handle welder_id specially (convert to ObjectId)
                if 'welder_id' in data:
                    try:
                        update_doc['welder_id'] = ObjectId(data['welder_id'])
                    except Exception:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid welder_id format'
                        }, status=400)
                
                # Update JSON fields
                json_fields = [
                    'basic_info', 'joints', 'base_metals', 'filler_metals', 'positions',
                    'preheat', 'post_weld_heat_treatment', 'gas', 'electrical_characteristics',
                    'techniques', 'welding_parameters', 'tensile_test', 'guided_bend_test',
                    'toughness_test', 'fillet_weld_test', 'other_tests', 'signatures'
                ]
                
                for field in json_fields:
                    if field in data:
                        parsed_value = parse_json_field(data[field])
                        update_doc[field] = parsed_value
                
                # Update boolean field
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active'].lower() in ['true', '1', 'yes']
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'No fields provided for update. Available fields: {list(data.keys())}. Please provide at least one field to update or upload files.'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = pqrs_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                # Get updated PQR document
                updated_pqr = pqrs_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'PQR updated successfully',
                    'data': {
                        'id': str(updated_pqr.get('_id', '')),
                        'type': updated_pqr.get('type', ''),
                        'lab_test_no': updated_pqr.get('lab_test_no', ''),
                        'joint_design_sketch': [f"{settings.MEDIA_URL}{file}" for file in updated_pqr.get('joint_design_sketch', [])],
                        'updated_at': updated_pqr.get('updated_at').isoformat() if updated_pqr.get('updated_at') else ''
                    }
                })
                
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Validation error: {str(e)}'
                }, status=400)
        
        elif request.method == 'DELETE':
            # Permanently delete the PQR and its image folder
            import os
            import shutil
            from django.conf import settings
            
            # Delete image folder if exists
            pqr_id = str(obj_id)
            media_folder_path = os.path.join(settings.MEDIA_ROOT, 'pqrs', pqr_id)
            if os.path.exists(media_folder_path):
                try:
                    shutil.rmtree(media_folder_path)
                except Exception as e:
                    # Log error but continue with deletion
                    pass
            
            # Delete the PQR document
            result = pqrs_collection.delete_one({'_id': obj_id})
            
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'PQR not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'PQR permanently deleted successfully',
                'data': {
                    'id': str(obj_id),
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
def pqr_search(request):
    """
    Search PQRs by various criteria
    Query parameters:
    - law_name: Search by law name (case-insensitive)
    - lab_test_no: Search by lab test number (case-insensitive)
    - type: Search by type (case-insensitive)
    - welder_id: Search by welder ID
    - q: Global search across all text fields (type, lab_test_no, law_name, mechanical_testing_conducted_by, welder_name)
    """
    try:
        # Get query parameters
        law_name = request.GET.get('law_name', '')
        lab_test_no = request.GET.get('lab_test_no', '')
        type_filter = request.GET.get('type', '')
        welder_id = request.GET.get('welder_id', '')
        q = request.GET.get('q', '')  # Global search parameter
        
        # Build query for raw MongoDB
        query = {}
        if law_name:
            query['law_name'] = {'$regex': law_name, '$options': 'i'}
        if lab_test_no:
            query['lab_test_no'] = {'$regex': lab_test_no, '$options': 'i'}
        if type_filter:
            query['type'] = {'$regex': type_filter, '$options': 'i'}
        if welder_id:
            try:
                query['welder_id'] = ObjectId(welder_id)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid welder_id format'
                }, status=400)
        
        # Handle global search parameter 'q'
        if q:
            # Create OR conditions for global search across multiple fields
            or_conditions = [
                {'type': {'$regex': q, '$options': 'i'}},
                {'lab_test_no': {'$regex': q, '$options': 'i'}},
                {'law_name': {'$regex': q, '$options': 'i'}},
                {'mechanical_testing_conducted_by': {'$regex': q, '$options': 'i'}}
            ]
            
            # Add welder name to global search
            try:
                welders_collection = db.welders
                welder_docs = welders_collection.find({
                    'operator_name': {'$regex': q, '$options': 'i'}
                })
                welder_ids = [doc['_id'] for doc in welder_docs]
                if welder_ids:
                    or_conditions.append({'welder_id': {'$in': welder_ids}})
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
        
        # Use raw query to search
        db = connection.get_db()
        pqrs_collection = db.pqrs
        
        pqrs = pqrs_collection.find(query)
        
        data = []
        for pqr_doc in pqrs:
            data.append({
                'id': str(pqr_doc.get('_id', '')),
                'type': pqr_doc.get('type', ''),
                'lab_test_no': pqr_doc.get('lab_test_no', ''),
                'law_name': pqr_doc.get('law_name', ''),
                'mechanical_testing_conducted_by': pqr_doc.get('mechanical_testing_conducted_by', ''),
                'is_active': pqr_doc.get('is_active', True),
                'created_at': pqr_doc.get('created_at').isoformat() if pqr_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'law_name': law_name,
                'lab_test_no': lab_test_no,
                'type': type_filter,
                'welder_id': welder_id,
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
def pqr_stats(request):
    """
    Get PQR statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        pqrs_collection = db.pqrs
        
        total_pqrs = pqrs_collection.count_documents({})
        
        # Count by type
        type_stats = pqrs_collection.aggregate([
            {'$match': {'type': {'$ne': ''}}},
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by law name
        law_stats = pqrs_collection.aggregate([
            {'$match': {'law_name': {'$ne': ''}}},
            {'$group': {'_id': '$law_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by mechanical testing conducted by
        tester_stats = pqrs_collection.aggregate([
            {'$match': {'mechanical_testing_conducted_by': {'$ne': ''}}},
            {'$group': {'_id': '$mechanical_testing_conducted_by', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_pqrs': total_pqrs,
                'type_distribution': list(type_stats),
                'law_distribution': list(law_stats),
                'tester_distribution': list(tester_stats)
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
def pqr_by_welder(request, welder_id):
    """
    Get all PQRs for a specific welder
    """
    try:
        # Validate ObjectId format
        try:
            welder_obj_id = ObjectId(welder_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid welder ID format: {welder_id}'
            }, status=400)
        
        # Verify welder exists
        try:
            welder = Welder.objects.get(id=welder_obj_id)
        except (DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Welder not found'
            }, status=404)
        
        # Use raw query to find PQRs by welder
        db = connection.get_db()
        pqrs_collection = db.pqrs
        
        pqrs = pqrs_collection.find({
            'welder_id': welder_obj_id
        })
        
        data = []
        for pqr_doc in pqrs:
            data.append({
                'id': str(pqr_doc.get('_id', '')),
                'type': pqr_doc.get('type', ''),
                'lab_test_no': pqr_doc.get('lab_test_no', ''),
                'law_name': pqr_doc.get('law_name', ''),
                'mechanical_testing_conducted_by': pqr_doc.get('mechanical_testing_conducted_by', ''),
                'is_active': pqr_doc.get('is_active', True),
                'created_at': pqr_doc.get('created_at').isoformat() if pqr_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'welder_info': {
                'welder_id': str(welder.id),
                'operator_name': welder.operator_name,
                'operator_id': welder.operator_id,
                'iqama': welder.iqama
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)