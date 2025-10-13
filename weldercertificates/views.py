from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import WelderCertificate, TestResult
from weldercards.models import WelderCard
from welders.models import Welder
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def welder_certificate_list(request):
    """
    List all welder certificates or create a new welder certificate
    GET: Returns list of all welder certificates with welder card and welder information
    POST: Creates a new welder certificate
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get search parameters
            law_name_search = request.GET.get('law_name', '')
            tested_by_search = request.GET.get('tested_by', '')
            date_of_test_search = request.GET.get('date_of_test', '')
            
            # Use raw query to get all active certificates
            db = connection.get_db()
            certificates_collection = db.welder_certificates
            
            # Build query based on search parameters
            query = {}
            if law_name_search:
                query['law_name'] = {'$regex': law_name_search, '$options': 'i'}
            if tested_by_search:
                query['tested_by'] = {'$regex': tested_by_search, '$options': 'i'}
            if date_of_test_search:
                query['date_of_test'] = date_of_test_search
            
            # Get total count for pagination
            total_records = certificates_collection.count_documents(query)
            
            # Get paginated certificates
            certificates = certificates_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for cert_doc in certificates:
                # Get welder card and welder information
                welder_card_info = {
                    'card_id': str(cert_doc.get('welder_card_id', '')),
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
                    card_obj_id = cert_doc.get('welder_card_id')
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
                    'id': str(cert_doc.get('_id', '')),
                    'welder_card_id': str(cert_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
                    'date_of_test': cert_doc.get('date_of_test', ''),
                    'identification_of_wps_pqr': cert_doc.get('identification_of_wps_pqr', ''),
                    'qualification_standard': cert_doc.get('qualification_standard', ''),
                    'base_metal_specification': cert_doc.get('base_metal_specification', ''),
                    'joint_type': cert_doc.get('joint_type', ''),
                    'weld_type': cert_doc.get('weld_type', ''),
                    'testing_variables_and_qualification_limits': cert_doc.get('testing_variables_and_qualification_limits', {}),
                    'tests': cert_doc.get('tests', []),
                    'law_name': cert_doc.get('law_name', ''),
                    'tested_by': cert_doc.get('tested_by', ''),
                    'witnessed_by': cert_doc.get('witnessed_by', ''),
                    'is_active': cert_doc.get('is_active', True),
                    'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else '',
                    'updated_at': cert_doc.get('updated_at').isoformat() if cert_doc.get('updated_at') else ''
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
                test_result = TestResult(
                    type=test_data.get('type', ''),
                    test_performed=test_data.get('test_performed', False),
                    results=test_data.get('results', ''),
                    report_no=test_data.get('report_no', '')
                )
                tests_list.append(test_result)
            
            certificate = WelderCertificate(
                welder_card_id=ObjectId(data['welder_card_id']),
                date_of_test=data.get('date_of_test', ''),
                identification_of_wps_pqr=data.get('identification_of_wps_pqr', ''),
                qualification_standard=data.get('qualification_standard', ''),
                base_metal_specification=data.get('base_metal_specification', ''),
                joint_type=data.get('joint_type', ''),
                weld_type=data.get('weld_type', ''),
                testing_variables_and_qualification_limits=data.get('testing_variables_and_qualification_limits', {}),
                tests=tests_list,
                law_name=data['law_name'],
                tested_by=data['tested_by'],
                witnessed_by=data['witnessed_by'],
                is_active=data.get('is_active', True)
            )
            certificate.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder certificate created successfully',
                'data': {
                    'id': str(certificate.id),
                    'law_name': certificate.law_name,
                    'date_of_test': certificate.date_of_test,
                    'tested_by': certificate.tested_by
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
def welder_certificate_detail(request, object_id):
    """
    Get, update, or delete a specific welder certificate by ObjectId
    GET: Returns certificate details with welder card and welder information
    PUT: Updates certificate information
    DELETE: Deletes the certificate
    """
    try:
        # Validate ObjectId format
        try:
            obj_id = ObjectId(object_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid certificate ID format: {object_id}'
            }, status=400)
        
        # Use raw query to find certificate by ObjectId
        db = connection.get_db()
        certificates_collection = db.welder_certificates
        
        cert_doc = certificates_collection.find_one({'_id': obj_id})
        if not cert_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Welder certificate not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get welder card and welder information
            welder_card_info = {
                'card_id': str(cert_doc.get('welder_card_id', '')),
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
                card_obj_id = cert_doc.get('welder_card_id')
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
                    'id': str(cert_doc.get('_id', '')),
                    'welder_card_id': str(cert_doc.get('welder_card_id', '')),
                    'welder_card_info': welder_card_info,
                    'date_of_test': cert_doc.get('date_of_test', ''),
                    'identification_of_wps_pqr': cert_doc.get('identification_of_wps_pqr', ''),
                    'qualification_standard': cert_doc.get('qualification_standard', ''),
                    'base_metal_specification': cert_doc.get('base_metal_specification', ''),
                    'joint_type': cert_doc.get('joint_type', ''),
                    'weld_type': cert_doc.get('weld_type', ''),
                    'testing_variables_and_qualification_limits': cert_doc.get('testing_variables_and_qualification_limits', {}),
                    'tests': cert_doc.get('tests', []),
                    'law_name': cert_doc.get('law_name', ''),
                    'tested_by': cert_doc.get('tested_by', ''),
                    'witnessed_by': cert_doc.get('witnessed_by', ''),
                    'is_active': cert_doc.get('is_active', True),
                    'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else '',
                    'updated_at': cert_doc.get('updated_at').isoformat() if cert_doc.get('updated_at') else ''
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
                if 'date_of_test' in data:
                    update_doc['date_of_test'] = data['date_of_test']
                if 'identification_of_wps_pqr' in data:
                    update_doc['identification_of_wps_pqr'] = data['identification_of_wps_pqr']
                if 'qualification_standard' in data:
                    update_doc['qualification_standard'] = data['qualification_standard']
                if 'base_metal_specification' in data:
                    update_doc['base_metal_specification'] = data['base_metal_specification']
                if 'joint_type' in data:
                    update_doc['joint_type'] = data['joint_type']
                if 'weld_type' in data:
                    update_doc['weld_type'] = data['weld_type']
                if 'testing_variables_and_qualification_limits' in data:
                    update_doc['testing_variables_and_qualification_limits'] = data['testing_variables_and_qualification_limits']
                if 'tests' in data:
                    # Process tests array
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
                if 'law_name' in data:
                    update_doc['law_name'] = data['law_name']
                if 'tested_by' in data:
                    update_doc['tested_by'] = data['tested_by']
                if 'witnessed_by' in data:
                    update_doc['witnessed_by'] = data['witnessed_by']
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active']
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = certificates_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated certificate document
                updated_cert = certificates_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Welder certificate updated successfully',
                    'data': {
                        'id': str(updated_cert.get('_id', '')),
                        'law_name': updated_cert.get('law_name', ''),
                        'date_of_test': updated_cert.get('date_of_test', ''),
                        'updated_at': updated_cert.get('updated_at').isoformat() if updated_cert.get('updated_at') else ''
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
            result = certificates_collection.delete_one(
                {'_id': obj_id}
            )
            
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Welder certificate not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder certificate deleted successfully',
                'data': {
                    'id': str(obj_id),
                    'law_name': cert_doc.get('law_name', ''),
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
def welder_certificate_search(request):
    """
    Search welder certificates by various criteria
    Query parameters:
    - law_name: Search by law name (case-insensitive)
    - tested_by: Search by tested by field (case-insensitive)
    - date_of_test: Search by date of test (exact match)
    - welder_card_id: Search by welder card ID
    """
    try:
        # Get query parameters
        law_name = request.GET.get('law_name', '')
        tested_by = request.GET.get('tested_by', '')
        date_of_test = request.GET.get('date_of_test', '')
        welder_card_id = request.GET.get('welder_card_id', '')
        
        # Build query for raw MongoDB
        query = {}
        if law_name:
            query['law_name'] = {'$regex': law_name, '$options': 'i'}
        if tested_by:
            query['tested_by'] = {'$regex': tested_by, '$options': 'i'}
        if date_of_test:
            query['date_of_test'] = date_of_test
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
        certificates_collection = db.welder_certificates
        
        certificates = certificates_collection.find(query)
        
        data = []
        for cert_doc in certificates:
            data.append({
                'id': str(cert_doc.get('_id', '')),
                'law_name': cert_doc.get('law_name', ''),
                'date_of_test': cert_doc.get('date_of_test', ''),
                'tested_by': cert_doc.get('tested_by', ''),
                'witnessed_by': cert_doc.get('witnessed_by', ''),
                'qualification_standard': cert_doc.get('qualification_standard', ''),
                'is_active': cert_doc.get('is_active', True),
                'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'law_name': law_name,
                'tested_by': tested_by,
                'date_of_test': date_of_test,
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
def welder_certificate_stats(request):
    """
    Get welder certificate statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        certificates_collection = db.welder_certificates
        
        total_certificates = certificates_collection.count_documents({})
        
        # Count by law name
        law_stats = certificates_collection.aggregate([
            {'$match': {'law_name': {'$ne': ''}}},
            {'$group': {'_id': '$law_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by tested_by
        tester_stats = certificates_collection.aggregate([
            {'$match': {'tested_by': {'$ne': ''}}},
            {'$group': {'_id': '$tested_by', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_certificates': total_certificates,
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
def welder_certificate_by_card(request, welder_card_id):
    """
    Get all certificates for a specific welder card
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
        
        # Use raw query to find certificates by welder card
        db = connection.get_db()
        certificates_collection = db.welder_certificates
        
        certificates = certificates_collection.find({
            'welder_card_id': card_obj_id
        })
        
        data = []
        for cert_doc in certificates:
            data.append({
                'id': str(cert_doc.get('_id', '')),
                'law_name': cert_doc.get('law_name', ''),
                'date_of_test': cert_doc.get('date_of_test', ''),
                'tested_by': cert_doc.get('tested_by', ''),
                'witnessed_by': cert_doc.get('witnessed_by', ''),
                'qualification_standard': cert_doc.get('qualification_standard', ''),
                'is_active': cert_doc.get('is_active', True),
                'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else ''
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