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
from weldercards.models import WelderCard
from welders.models import Welder
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def pqr_list(request):
    """
    List all PQRs or create a new PQR
    GET: Returns list of all PQRs with welder card and welder information
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
            
            # Get total count for pagination
            total_records = pqrs_collection.count_documents(query)
            
            # Get paginated PQRs
            pqrs = pqrs_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for pqr_doc in pqrs:
                # Get welder card and welder information
                welder_card_info = {
                    'card_id': str(pqr_doc.get('welder_card_id', '')),
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
                    card_obj_id = pqr_doc.get('welder_card_id')
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
                    'id': str(pqr_doc.get('_id', '')),
                    'type': pqr_doc.get('type', ''),
                    'basic_info': pqr_doc.get('basic_info', {}),
                    'joints': pqr_doc.get('joints', {}),
                    'joint_design_sketch': pqr_doc.get('joint_design_sketch', ''),
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
                    'welder_card_id': str(pqr_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
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
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['type', 'welder_card_id', 'mechanical_testing_conducted_by', 'lab_test_no', 'law_name']
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
            
            pqr = PQR(
                type=data['type'],
                basic_info=data.get('basic_info', {}),
                joints=data.get('joints', {}),
                joint_design_sketch=data.get('joint_design_sketch', ''),
                base_metals=data.get('base_metals', {}),
                filler_metals=data.get('filler_metals', {}),
                positions=data.get('positions', {}),
                preheat=data.get('preheat', {}),
                post_weld_heat_treatment=data.get('post_weld_heat_treatment', {}),
                gas=data.get('gas', {}),
                electrical_characteristics=data.get('electrical_characteristics', {}),
                techniques=data.get('techniques', {}),
                welding_parameters=data.get('welding_parameters', {}),
                tensile_test=data.get('tensile_test', {}),
                guided_bend_test=data.get('guided_bend_test', {}),
                toughness_test=data.get('toughness_test', {}),
                fillet_weld_test=data.get('fillet_weld_test', {}),
                other_tests=data.get('other_tests', {}),
                welder_card_id=ObjectId(data['welder_card_id']),
                mechanical_testing_conducted_by=data['mechanical_testing_conducted_by'],
                lab_test_no=data['lab_test_no'],
                law_name=data['law_name'],
                signatures=data.get('signatures', {}),
                is_active=data.get('is_active', True)
            )
            pqr.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'PQR created successfully',
                'data': {
                    'id': str(pqr.id),
                    'type': pqr.type,
                    'lab_test_no': pqr.lab_test_no,
                    'law_name': pqr.law_name
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
def pqr_detail(request, object_id):
    """
    Get, update, or delete a specific PQR by ObjectId
    GET: Returns PQR details with welder card and welder information
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
            # Get welder card and welder information
            welder_card_info = {
                'card_id': str(pqr_doc.get('welder_card_id', '')),
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
                card_obj_id = pqr_doc.get('welder_card_id')
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
                    'id': str(pqr_doc.get('_id', '')),
                    'type': pqr_doc.get('type', ''),
                    'basic_info': pqr_doc.get('basic_info', {}),
                    'joints': pqr_doc.get('joints', {}),
                    'joint_design_sketch': pqr_doc.get('joint_design_sketch', ''),
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
                    'welder_card_id': str(pqr_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
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
                    'type', 'basic_info', 'joints', 'joint_design_sketch', 'base_metals',
                    'filler_metals', 'positions', 'preheat', 'post_weld_heat_treatment',
                    'gas', 'electrical_characteristics', 'techniques', 'welding_parameters',
                    'tensile_test', 'guided_bend_test', 'toughness_test', 'fillet_weld_test',
                    'other_tests', 'mechanical_testing_conducted_by', 'lab_test_no',
                    'law_name', 'signatures', 'is_active'
                ]
                
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = pqrs_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated PQR document
                updated_pqr = pqrs_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'PQR updated successfully',
                    'data': {
                        'id': str(updated_pqr.get('_id', '')),
                        'type': updated_pqr.get('type', ''),
                        'lab_test_no': updated_pqr.get('lab_test_no', ''),
                        'updated_at': updated_pqr.get('updated_at').isoformat() if updated_pqr.get('updated_at') else ''
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
            result = pqrs_collection.delete_one(
                {'_id': obj_id}
            )
            
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'PQR not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'PQR deleted successfully',
                'data': {
                    'id': str(obj_id),
                    'lab_test_no': pqr_doc.get('lab_test_no', ''),
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
    - welder_card_id: Search by welder card ID
    """
    try:
        # Get query parameters
        law_name = request.GET.get('law_name', '')
        lab_test_no = request.GET.get('lab_test_no', '')
        type_filter = request.GET.get('type', '')
        welder_card_id = request.GET.get('welder_card_id', '')
        
        # Build query for raw MongoDB
        query = {}
        if law_name:
            query['law_name'] = {'$regex': law_name, '$options': 'i'}
        if lab_test_no:
            query['lab_test_no'] = {'$regex': lab_test_no, '$options': 'i'}
        if type_filter:
            query['type'] = {'$regex': type_filter, '$options': 'i'}
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
def pqr_by_card(request, welder_card_id):
    """
    Get all PQRs for a specific welder card
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
        
        # Use raw query to find PQRs by welder card
        db = connection.get_db()
        pqrs_collection = db.pqrs
        
        pqrs = pqrs_collection.find({
            'welder_card_id': card_obj_id
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