from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError

from .models import TestingReport, TestResult
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def testing_report_list(request):
    """
    List all testing reports or create a new testing report
    GET: Returns list of all testing reports with welder information
    POST: Creates a new testing report
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get search parameters
            client_name_search = request.GET.get('client_name', '')
            prepared_by_search = request.GET.get('prepared_by', '')
            welder_name_search = request.GET.get('welder_name', '')
            
            # Get filtering parameters
            show_inactive = request.GET.get('show_inactive', '').lower() == 'true'
            include_inactive = request.GET.get('include_inactive', '').lower() == 'true'
            
            # Use raw query to get all active testing reports
            db = connection.get_db()
            testing_reports_collection = db.testing_reports
            
            # Build query based on search parameters
            query = {}
            if client_name_search:
                query['client_name'] = {'$regex': client_name_search, '$options': 'i'}
            if prepared_by_search:
                query['prepared_by'] = {'$regex': prepared_by_search, '$options': 'i'}
            if welder_name_search:
                query['results.welder_name'] = {'$regex': welder_name_search, '$options': 'i'}
            
            # Add filtering based on is_active status
            if show_inactive:
                # Only show inactive testing reports
                query['is_active'] = False
            elif include_inactive:
                # Show both active and inactive testing reports (no filter)
                pass
            else:
                # Default: only show active testing reports
                query['is_active'] = True
            
            # Get total count for pagination
            total_records = testing_reports_collection.count_documents(query)
            
            # Get paginated testing reports
            testing_reports = testing_reports_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for report_doc in testing_reports:
                # Get welder information from results
                welders_info = []
                for result in report_doc.get('results', []):
                    welders_info.append({
                        'welder_id': result.get('welder_id', ''),
                        'welder_name': result.get('welder_name', ''),
                        'iqama_number': result.get('iqama_number', ''),
                        'test_coupon_id': result.get('test_coupon_id', ''),
                        'result_status': result.get('result_status', '')
                    })
                
                data.append({
                    'id': str(report_doc.get('_id', '')),
                    'results': report_doc.get('results', []),
                    'welders_info': welders_info,
                    'prepared_by': report_doc.get('prepared_by', ''),
                    'client_name': report_doc.get('client_name', ''),
                    'project_details': report_doc.get('project_details', ''),
                    'contract_details': report_doc.get('contract_details', ''),
                    'welders_count': len(report_doc.get('results', [])),
                    'is_active': report_doc.get('is_active', True),
                    'created_at': report_doc.get('created_at').isoformat() if report_doc.get('created_at') else '',
                    'updated_at': report_doc.get('updated_at').isoformat() if report_doc.get('updated_at') else ''
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
            required_fields = ['results', 'prepared_by', 'client_name']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Process results array
            results_list = []
            for result_data in data['results']:
                # Validate required fields for each result
                required_result_fields = ['welder_id', 'welder_name', 'iqama_number', 'test_coupon_id', 'result_status']
                for field in required_result_fields:
                    if field not in result_data or not result_data[field]:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Required field "{field}" is missing or empty in results'
                        }, status=400)
                
                test_result = TestResult(
                    welder_id=result_data['welder_id'],
                    welder_name=result_data['welder_name'],
                    iqama_number=result_data['iqama_number'],
                    test_coupon_id=result_data['test_coupon_id'],
                    date_of_inspection=result_data.get('date_of_inspection', ''),
                    welding_processes=result_data.get('welding_processes', ''),
                    type_of_welding=result_data.get('type_of_welding', ''),
                    backing=result_data.get('backing', ''),
                    type_of_weld_joint=result_data.get('type_of_weld_joint', ''),
                    thickness_product_type=result_data.get('thickness_product_type', ''),
                    diameter_of_pipe=result_data.get('diameter_of_pipe', ''),
                    base_metal_p_number=result_data.get('base_metal_p_number', ''),
                    filler_metal_electrode_spec=result_data.get('filler_metal_electrode_spec', ''),
                    filler_metal_f_number=result_data.get('filler_metal_f_number', ''),
                    filler_metal_addition_deletion=result_data.get('filler_metal_addition_deletion', ''),
                    deposit_thickness_for_each_process=result_data.get('deposit_thickness_for_each_process', ''),
                    welding_positions=result_data.get('welding_positions', ''),
                    vertical_progression=result_data.get('vertical_progression', ''),
                    type_of_fuel_gas=result_data.get('type_of_fuel_gas', ''),
                    inert_gas_backing=result_data.get('inert_gas_backing', ''),
                    transfer_mode=result_data.get('transfer_mode', ''),
                    current_type_polarity=result_data.get('current_type_polarity', ''),
                    voltage=result_data.get('voltage', ''),
                    current=result_data.get('current', ''),
                    travel_speed=result_data.get('travel_speed', ''),
                    interpass_temperature=result_data.get('interpass_temperature', ''),
                    pre_heat=result_data.get('pre_heat', ''),
                    post_weld_heat_treatment=result_data.get('post_weld_heat_treatment', ''),
                    result_status=result_data['result_status']
                )
                results_list.append(test_result)
            
            testing_report = TestingReport(
                results=results_list,
                prepared_by=data['prepared_by'],
                client_name=data['client_name'],
                project_details=data.get('project_details', ''),
                contract_details=data.get('contract_details', ''),
                is_active=data.get('is_active', True)
            )
            testing_report.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Testing report created successfully',
                'data': {
                    'id': str(testing_report.id),
                    'client_name': testing_report.client_name,
                    'welders_count': len(testing_report.results),
                    'prepared_by': testing_report.prepared_by
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
def testing_report_detail(request, object_id):
    """
    Get, update, or delete a specific testing report by ObjectId
    GET: Returns testing report details with all welder information
    PUT: Updates testing report information
    DELETE: Deletes the testing report
    """
    try:
        # Validate ObjectId format
        try:
            obj_id = ObjectId(object_id)
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid testing report ID format: {object_id}'
            }, status=400)
        
        # Use raw query to find testing report by ObjectId
        db = connection.get_db()
        testing_reports_collection = db.testing_reports
        
        report_doc = testing_reports_collection.find_one({'_id': obj_id})
        if not report_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Testing report not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get welder information from results
            welders_info = []
            for result in report_doc.get('results', []):
                welders_info.append({
                    'welder_id': result.get('welder_id', ''),
                    'welder_name': result.get('welder_name', ''),
                    'iqama_number': result.get('iqama_number', ''),
                    'test_coupon_id': result.get('test_coupon_id', ''),
                    'result_status': result.get('result_status', ''),
                    'date_of_inspection': result.get('date_of_inspection', ''),
                    'welding_processes': result.get('welding_processes', ''),
                    'type_of_welding': result.get('type_of_welding', '')
                })
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(report_doc.get('_id', '')),
                    'results': report_doc.get('results', []),
                    'welders_info': welders_info,
                    'prepared_by': report_doc.get('prepared_by', ''),
                    'client_name': report_doc.get('client_name', ''),
                    'project_details': report_doc.get('project_details', ''),
                    'contract_details': report_doc.get('contract_details', ''),
                    'welders_count': len(report_doc.get('results', [])),
                    'is_active': report_doc.get('is_active', True),
                    'created_at': report_doc.get('created_at').isoformat() if report_doc.get('created_at') else '',
                    'updated_at': report_doc.get('updated_at').isoformat() if report_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update fields if provided
                if 'prepared_by' in data:
                    update_doc['prepared_by'] = data['prepared_by']
                if 'client_name' in data:
                    update_doc['client_name'] = data['client_name']
                if 'project_details' in data:
                    update_doc['project_details'] = data['project_details']
                if 'contract_details' in data:
                    update_doc['contract_details'] = data['contract_details']
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active']
                
                # Handle results array update
                if 'results' in data:
                    results_list = []
                    for result_data in data['results']:
                        # Validate required fields for each result
                        required_result_fields = ['welder_id', 'welder_name', 'iqama_number', 'test_coupon_id', 'result_status']
                        for field in required_result_fields:
                            if field not in result_data or not result_data[field]:
                                return JsonResponse({
                                    'status': 'error',
                                    'message': f'Required field "{field}" is missing or empty in results'
                                }, status=400)
                        
                        result = {
                            'welder_id': result_data['welder_id'],
                            'welder_name': result_data['welder_name'],
                            'iqama_number': result_data['iqama_number'],
                            'test_coupon_id': result_data['test_coupon_id'],
                            'date_of_inspection': result_data.get('date_of_inspection', ''),
                            'welding_processes': result_data.get('welding_processes', ''),
                            'type_of_welding': result_data.get('type_of_welding', ''),
                            'backing': result_data.get('backing', ''),
                            'type_of_weld_joint': result_data.get('type_of_weld_joint', ''),
                            'thickness_product_type': result_data.get('thickness_product_type', ''),
                            'diameter_of_pipe': result_data.get('diameter_of_pipe', ''),
                            'base_metal_p_number': result_data.get('base_metal_p_number', ''),
                            'filler_metal_electrode_spec': result_data.get('filler_metal_electrode_spec', ''),
                            'filler_metal_f_number': result_data.get('filler_metal_f_number', ''),
                            'filler_metal_addition_deletion': result_data.get('filler_metal_addition_deletion', ''),
                            'deposit_thickness_for_each_process': result_data.get('deposit_thickness_for_each_process', ''),
                            'welding_positions': result_data.get('welding_positions', ''),
                            'vertical_progression': result_data.get('vertical_progression', ''),
                            'type_of_fuel_gas': result_data.get('type_of_fuel_gas', ''),
                            'inert_gas_backing': result_data.get('inert_gas_backing', ''),
                            'transfer_mode': result_data.get('transfer_mode', ''),
                            'current_type_polarity': result_data.get('current_type_polarity', ''),
                            'voltage': result_data.get('voltage', ''),
                            'current': result_data.get('current', ''),
                            'travel_speed': result_data.get('travel_speed', ''),
                            'interpass_temperature': result_data.get('interpass_temperature', ''),
                            'pre_heat': result_data.get('pre_heat', ''),
                            'post_weld_heat_treatment': result_data.get('post_weld_heat_treatment', ''),
                            'result_status': result_data['result_status']
                        }
                        results_list.append(result)
                    update_doc['results'] = results_list
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = testing_reports_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated testing report document
                updated_report = testing_reports_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Testing report updated successfully',
                    'data': {
                        'id': str(updated_report.get('_id', '')),
                        'client_name': updated_report.get('client_name', ''),
                        'welders_count': len(updated_report.get('results', [])),
                        'updated_at': updated_report.get('updated_at').isoformat() if updated_report.get('updated_at') else ''
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
            # Soft delete: set is_active to false instead of hard delete
            result = testing_reports_collection.update_one(
                {'_id': obj_id},
                {
                    '$set': {
                        'is_active': False,
                        'updated_at': datetime.now()
                    }
                }
            )
            
            if result.matched_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Testing report not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Testing report deactivated successfully',
                'data': {
                    'id': str(obj_id),
                    'report_no': report_doc.get('report_no', ''),
                    'is_active': False,
                    'deactivated_at': datetime.now().isoformat()
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
def testing_report_search(request):
    """
    Search testing reports by various criteria
    Query parameters:
    - client_name: Search by client name (case-insensitive)
    - prepared_by: Search by prepared by field (case-insensitive)
    - welder_name: Search by welder name in results (case-insensitive)
    - welder_id: Search by welder ID in results
    """
    try:
        # Get query parameters
        client_name = request.GET.get('client_name', '')
        prepared_by = request.GET.get('prepared_by', '')
        welder_name = request.GET.get('welder_name', '')
        welder_id = request.GET.get('welder_id', '')
        
        # Build query for raw MongoDB
        query = {}
        if client_name:
            query['client_name'] = {'$regex': client_name, '$options': 'i'}
        if prepared_by:
            query['prepared_by'] = {'$regex': prepared_by, '$options': 'i'}
        if welder_name:
            query['results.welder_name'] = {'$regex': welder_name, '$options': 'i'}
        if welder_id:
            query['results.welder_id'] = welder_id
        
        # Use raw query to search
        db = connection.get_db()
        testing_reports_collection = db.testing_reports
        
        testing_reports = testing_reports_collection.find(query)
        
        data = []
        for report_doc in testing_reports:
            # Get welder information from results
            welders_info = []
            for result in report_doc.get('results', []):
                welders_info.append({
                    'welder_id': result.get('welder_id', ''),
                    'welder_name': result.get('welder_name', ''),
                    'iqama_number': result.get('iqama_number', ''),
                    'result_status': result.get('result_status', '')
                })
            
            data.append({
                'id': str(report_doc.get('_id', '')),
                'client_name': report_doc.get('client_name', ''),
                'prepared_by': report_doc.get('prepared_by', ''),
                'welders_info': welders_info,
                'welders_count': len(report_doc.get('results', [])),
                'is_active': report_doc.get('is_active', True),
                'created_at': report_doc.get('created_at').isoformat() if report_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'client_name': client_name,
                'prepared_by': prepared_by,
                'welder_name': welder_name,
                'welder_id': welder_id
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
def testing_report_stats(request):
    """
    Get testing report statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        testing_reports_collection = db.testing_reports
        
        total_reports = testing_reports_collection.count_documents({})
        
        # Count by client
        client_stats = testing_reports_collection.aggregate([
            {'$match': {'client_name': {'$ne': ''}}},
            {'$group': {'_id': '$client_name', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count by prepared_by
        preparer_stats = testing_reports_collection.aggregate([
            {'$match': {'prepared_by': {'$ne': ''}}},
            {'$group': {'_id': '$prepared_by', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        # Count total welders tested
        total_welders = testing_reports_collection.aggregate([
            {'$project': {'welders_count': {'$size': '$results'}}},
            {'$group': {'_id': None, 'total_welders': {'$sum': '$welders_count'}}}
        ])
        
        total_welders_count = 0
        for stat in total_welders:
            total_welders_count = stat.get('total_welders', 0)
            break
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_reports': total_reports,
                'total_welders_tested': total_welders_count,
                'client_distribution': list(client_stats),
                'preparer_distribution': list(preparer_stats)
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
def testing_report_by_welder(request, welder_id):
    """
    Get all testing reports for a specific welder
    """
    try:
        # Use raw query to find testing reports by welder
        db = connection.get_db()
        testing_reports_collection = db.testing_reports
        
        testing_reports = testing_reports_collection.find({
            'results.welder_id': welder_id
        })
        
        data = []
        for report_doc in testing_reports:
            # Find the specific welder's result in this report
            welder_result = None
            for result in report_doc.get('results', []):
                if result.get('welder_id') == welder_id:
                    welder_result = result
                    break
            
            data.append({
                'id': str(report_doc.get('_id', '')),
                'client_name': report_doc.get('client_name', ''),
                'prepared_by': report_doc.get('prepared_by', ''),
                'welder_result': welder_result,
                'project_details': report_doc.get('project_details', ''),
                'contract_details': report_doc.get('contract_details', ''),
                'is_active': report_doc.get('is_active', True),
                'created_at': report_doc.get('created_at').isoformat() if report_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'welder_id': welder_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)