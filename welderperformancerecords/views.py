from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import WelderPerformanceRecord, PerformanceTestResult
from weldercards.models import WelderCard
from welders.models import Welder
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def welder_performance_record_list(request):
    """
    List all welder performance records or create a new performance record
    GET: Returns list of all performance records with welder card and welder information
    POST: Creates a new performance record
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get search parameters
            law_name_search = request.GET.get('law_name', '')
            tested_by_search = request.GET.get('tested_by', '')
            date_of_welding_search = request.GET.get('date_of_welding', '')
            
            # Use raw query to get all active performance records
            db = connection.get_db()
            performance_records_collection = db.welder_performance_records
            
            # Build query based on search parameters
            query = {}
            if law_name_search:
                query['law_name'] = {'$regex': law_name_search, '$options': 'i'}
            if tested_by_search:
                query['tested_by'] = {'$regex': tested_by_search, '$options': 'i'}
            if date_of_welding_search:
                query['date_of_welding'] = date_of_welding_search
            
            # Get total count for pagination
            total_records = performance_records_collection.count_documents(query)
            
            # Get paginated performance records
            performance_records = performance_records_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for record_doc in performance_records:
                # Get welder card and welder information
                welder_card_info = {
                    'card_id': str(record_doc.get('welder_card_id', '')),
                    'card_no': 'Unknown',
                    'company': 'Unknown',
                    'welder_info': {
                        'welder_id': '',
                        'operator_name': 'Unknown Welder',
                        'operator_id': '',
                        'iqama': ''
                    }
                }
                
                try:
                    # Get welder card information
                    welder_cards_collection = db.welder_cards
                    card_obj_id = record_doc.get('welder_card_id')
                    if card_obj_id:
                        if isinstance(card_obj_id, str):
                            card_obj_id = ObjectId(card_obj_id)
                        card_doc = welder_cards_collection.find_one({'_id': card_obj_id})
                        if card_doc:
                            welder_card_info.update({
                                'card_no': card_doc.get('card_no', 'Unknown'),
                                'company': card_doc.get('company', 'Unknown')
                            })
                            
                            # Get welder information
                            welder_obj_id = card_doc.get('welder_id')
                            if welder_obj_id:
                                if isinstance(welder_obj_id, str):
                                    welder_obj_id = ObjectId(welder_obj_id)
                                welders_collection = db.welders
                                welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                                if welder_doc:
                                    welder_card_info['welder_info'] = {
                                        'welder_id': str(welder_doc.get('_id', '')),
                                        'operator_name': welder_doc.get('operator_name', 'Unknown Welder'),
                                        'operator_id': welder_doc.get('operator_id', ''),
                                        'iqama': welder_doc.get('iqama', '')
                                    }
                except Exception:
                    pass
                
                data.append({
                    'id': str(record_doc.get('_id', '')),
                    'welder_card_id': str(record_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
                    'wps_followed_date': record_doc.get('wps_followed_date', ''),
                    'date_of_issue': record_doc.get('date_of_issue', ''),
                    'date_of_welding': record_doc.get('date_of_welding', ''),
                    'joint_weld_type': record_doc.get('joint_weld_type', ''),
                    'base_metal_spec': record_doc.get('base_metal_spec', ''),
                    'base_metal_p_no': record_doc.get('base_metal_p_no', ''),
                    'filler_sfa_spec': record_doc.get('filler_sfa_spec', ''),
                    'filler_class_aws': record_doc.get('filler_class_aws', ''),
                    'test_coupon_size': record_doc.get('test_coupon_size', ''),
                    'positions': record_doc.get('positions', ''),
                    'testing_variables_and_qualification_limits': record_doc.get('testing_variables_and_qualification_limits', {}),
                    'tests': record_doc.get('tests', []),
                    'law_name': record_doc.get('law_name', ''),
                    'tested_by': record_doc.get('tested_by', ''),
                    'witnessed_by': record_doc.get('witnessed_by', ''),
                    'is_active': record_doc.get('is_active', True),
                    'created_at': record_doc.get('created_at').isoformat() if record_doc.get('created_at') else '',
                    'updated_at': record_doc.get('updated_at').isoformat() if record_doc.get('updated_at') else ''
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
            required_fields = ['welder_card_id', 'law_name', 'tested_by', 'witnessed_by', 'tests']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate that the welder card exists
            try:
                welder_card = WelderCard.objects.get(id=ObjectId(data['welder_card_id']))
            except (DoesNotExist, Exception) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Welder card not found: {str(e)}'
                }, status=400)
            
            # Process tests array
            tests_list = []
            for test_data in data['tests']:
                test_result = PerformanceTestResult(
                    type=test_data.get('type', ''),
                    test_performed=test_data.get('test_performed', False),
                    results=test_data.get('results', ''),
                    report_no=test_data.get('report_no', '')
                )
                tests_list.append(test_result)
            
            performance_record = WelderPerformanceRecord(
                welder_card_id=ObjectId(data['welder_card_id']),
                wps_followed_date=data.get('wps_followed_date', ''),
                date_of_issue=data.get('date_of_issue', ''),
                date_of_welding=data.get('date_of_welding', ''),
                joint_weld_type=data.get('joint_weld_type', ''),
                base_metal_spec=data.get('base_metal_spec', ''),
                base_metal_p_no=data.get('base_metal_p_no', ''),
                filler_sfa_spec=data.get('filler_sfa_spec', ''),
                filler_class_aws=data.get('filler_class_aws', ''),
                test_coupon_size=data.get('test_coupon_size', ''),
                positions=data.get('positions', ''),
                testing_variables_and_qualification_limits=data.get('testing_variables_and_qualification_limits', {}),
                tests=tests_list,
                law_name=data['law_name'],
                tested_by=data['tested_by'],
                witnessed_by=data['witnessed_by'],
                is_active=data.get('is_active', True)
            )
            performance_record.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder performance record created successfully',
                'data': {
                    'id': str(performance_record.id),
                    'law_name': performance_record.law_name,
                    'date_of_welding': performance_record.date_of_welding,
                    'tested_by': performance_record.tested_by
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
def welder_performance_record_detail(request, object_id):
    """
    Get, update, or delete a specific welder performance record by ObjectId
    GET: Returns performance record details with welder card and welder information
    PUT: Updates performance record information
    DELETE: Deletes the performance record
    """
    try:
        # Validate ObjectId format
        try:
            obj_id = ObjectId(object_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid performance record ID format: {object_id}'
            }, status=400)
        
        # Use raw query to find performance record by ObjectId
        db = connection.get_db()
        performance_records_collection = db.welder_performance_records
        
        record_doc = performance_records_collection.find_one({'_id': obj_id})
        if not record_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Welder performance record not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get welder card and welder information
            welder_card_info = {
                'card_id': str(record_doc.get('welder_card_id', '')),
                'card_no': 'Unknown',
                'company': 'Unknown',
                'welder_info': {
                    'welder_id': '',
                    'operator_name': 'Unknown Welder',
                    'operator_id': '',
                    'iqama': ''
                }
            }
            
            try:
                # Get welder card information
                welder_cards_collection = db.welder_cards
                card_obj_id = record_doc.get('welder_card_id')
                if card_obj_id:
                    if isinstance(card_obj_id, str):
                        card_obj_id = ObjectId(card_obj_id)
                    card_doc = welder_cards_collection.find_one({'_id': card_obj_id})
                    if card_doc:
                        welder_card_info.update({
                            'card_no': card_doc.get('card_no', 'Unknown'),
                            'company': card_doc.get('company', 'Unknown'),
                            'authorized_by': card_doc.get('authorized_by', ''),
                            'welding_inspector': card_doc.get('welding_inspector', '')
                        })
                        
                        # Get welder information
                        welder_obj_id = card_doc.get('welder_id')
                        if welder_obj_id:
                            if isinstance(welder_obj_id, str):
                                welder_obj_id = ObjectId(welder_obj_id)
                            welders_collection = db.welders
                            welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                            if welder_doc:
                                welder_card_info['welder_info'] = {
                                    'welder_id': str(welder_doc.get('_id', '')),
                                    'operator_name': welder_doc.get('operator_name', 'Unknown Welder'),
                                    'operator_id': welder_doc.get('operator_id', ''),
                                    'iqama': welder_doc.get('iqama', ''),
                                    'profile_image': welder_doc.get('profile_image', '')
                                }
            except Exception:
                pass
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(record_doc.get('_id', '')),
                    'welder_card_id': str(record_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
                    'wps_followed_date': record_doc.get('wps_followed_date', ''),
                    'date_of_issue': record_doc.get('date_of_issue', ''),
                    'date_of_welding': record_doc.get('date_of_welding', ''),
                    'joint_weld_type': record_doc.get('joint_weld_type', ''),
                    'base_metal_spec': record_doc.get('base_metal_spec', ''),
                    'base_metal_p_no': record_doc.get('base_metal_p_no', ''),
                    'filler_sfa_spec': record_doc.get('filler_sfa_spec', ''),
                    'filler_class_aws': record_doc.get('filler_class_aws', ''),
                    'test_coupon_size': record_doc.get('test_coupon_size', ''),
                    'positions': record_doc.get('positions', ''),
                    'testing_variables_and_qualification_limits': record_doc.get('testing_variables_and_qualification_limits', {}),
                    'tests': record_doc.get('tests', []),
                    'law_name': record_doc.get('law_name', ''),
                    'tested_by': record_doc.get('tested_by', ''),
                    'witnessed_by': record_doc.get('witnessed_by', ''),
                    'is_active': record_doc.get('is_active', True),
                    'created_at': record_doc.get('created_at').isoformat() if record_doc.get('created_at') else '',
                    'updated_at': record_doc.get('updated_at').isoformat() if record_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update welder_card_id if provided
                if 'welder_card_id' in data:
                    try:
                        welder_card = WelderCard.objects.get(id=ObjectId(data['welder_card_id']))
                        update_doc['welder_card_id'] = ObjectId(data['welder_card_id'])
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Welder card not found'
                        }, status=404)
                
                # Update other fields if provided
                update_fields = [
                    'wps_followed_date', 'date_of_issue', 'date_of_welding', 'joint_weld_type',
                    'base_metal_spec', 'base_metal_p_no', 'filler_sfa_spec', 'filler_class_aws',
                    'test_coupon_size', 'positions', 'testing_variables_and_qualification_limits',
                    'law_name', 'tested_by', 'witnessed_by', 'is_active'
                ]
                
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Handle tests array update
                if 'tests' in data:
                    tests_list = []
                    for test_data in data['tests']:
                        test_result = {
                            'type': test_data.get('type', ''),
                            'test_performed': test_data.get('test_performed', False),
                            'results': test_data.get('results', ''),
                            'report_no': test_data.get('report_no', '')
                        }
                        tests_list.append(test_result)
                    update_doc['tests'] = tests_list
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = performance_records_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated performance record document
                updated_record = performance_records_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Welder performance record updated successfully',
                    'data': {
                        'id': str(updated_record.get('_id', '')),
                        'law_name': updated_record.get('law_name', ''),
                        'date_of_welding': updated_record.get('date_of_welding', ''),
                        'updated_at': updated_record.get('updated_at').isoformat() if updated_record.get('updated_at') else ''
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
            # Delete the document completely
            result = performance_records_collection.delete_one(
                {'_id': obj_id}
            )
            
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Welder performance record not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder performance record deleted successfully',
                'data': {
                    'id': str(obj_id),
                    'law_name': record_doc.get('law_name', ''),
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
def welder_performance_record_search(request):
    """
    Search welder performance records by various criteria
    Query parameters:
    - law_name: Search by law name (case-insensitive)
    - tested_by: Search by tested by field (case-insensitive)
    - date_of_welding: Search by date of welding (exact match)
    - welder_card_id: Search by welder card ID
    """
    try:
        # Get query parameters
        law_name = request.GET.get('law_name', '')
        tested_by = request.GET.get('tested_by', '')
        date_of_welding = request.GET.get('date_of_welding', '')
        welder_card_id = request.GET.get('welder_card_id', '')
        
        # Build query for raw MongoDB
        query = {}
        if law_name:
            query['law_name'] = {'$regex': law_name, '$options': 'i'}
        if tested_by:
            query['tested_by'] = {'$regex': tested_by, '$options': 'i'}
        if date_of_welding:
            query['date_of_welding'] = date_of_welding
        if welder_card_id:
            try:
                query['welder_card_id'] = ObjectId(welder_card_id)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid welder_card_id format'
                }, status=400)
        
        # Use raw query to search
        db = connection.get_db()
        performance_records_collection = db.welder_performance_records
        
        performance_records = performance_records_collection.find(query)
        
        data = []
        for record_doc in performance_records:
            data.append({
                'id': str(record_doc.get('_id', '')),
                'law_name': record_doc.get('law_name', ''),
                'date_of_welding': record_doc.get('date_of_welding', ''),
                'tested_by': record_doc.get('tested_by', ''),
                'witnessed_by': record_doc.get('witnessed_by', ''),
                'joint_weld_type': record_doc.get('joint_weld_type', ''),
                'base_metal_spec': record_doc.get('base_metal_spec', ''),
                'is_active': record_doc.get('is_active', True),
                'created_at': record_doc.get('created_at').isoformat() if record_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'law_name': law_name,
                'tested_by': tested_by,
                'date_of_welding': date_of_welding,
                'welder_card_id': welder_card_id
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
def welder_performance_record_stats(request):
    """
    Get welder performance record statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        performance_records_collection = db.welder_performance_records
        
        total_records = performance_records_collection.count_documents({})
        
        # Count by law name
        law_stats = performance_records_collection.aggregate([
            {'$match': {'law_name': {'$ne': ''}}},
            {'$group': {'_id': '$law_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by tested_by
        tester_stats = performance_records_collection.aggregate([
            {'$match': {'tested_by': {'$ne': ''}}},
            {'$group': {'_id': '$tested_by', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_records': total_records,
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
def welder_performance_record_by_card(request, welder_card_id):
    """
    Get all performance records for a specific welder card
    """
    try:
        # Validate ObjectId format
        try:
            card_obj_id = ObjectId(welder_card_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid welder card ID format: {welder_card_id}'
            }, status=400)
        
        # Verify welder card exists
        try:
            welder_card = WelderCard.objects.get(id=card_obj_id)
        except (DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Welder card not found'
            }, status=404)
        
        # Use raw query to find performance records by welder card
        db = connection.get_db()
        performance_records_collection = db.welder_performance_records
        
        performance_records = performance_records_collection.find({
            'welder_card_id': card_obj_id
        })
        
        data = []
        for record_doc in performance_records:
            data.append({
                'id': str(record_doc.get('_id', '')),
                'law_name': record_doc.get('law_name', ''),
                'date_of_welding': record_doc.get('date_of_welding', ''),
                'tested_by': record_doc.get('tested_by', ''),
                'witnessed_by': record_doc.get('witnessed_by', ''),
                'joint_weld_type': record_doc.get('joint_weld_type', ''),
                'base_metal_spec': record_doc.get('base_metal_spec', ''),
                'is_active': record_doc.get('is_active', True),
                'created_at': record_doc.get('created_at').isoformat() if record_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'welder_card_info': {
                'card_id': str(welder_card.id),
                'card_no': welder_card.card_no,
                'company': welder_card.company
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)