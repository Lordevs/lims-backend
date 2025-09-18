from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from .models import Certificate
from samplepreperation.models import SamplePreparation


# ============= CERTIFICATE CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
def certificate_list(request):
    """
    List all certificates or create a new certificate
    GET: Returns list of all certificates with sample preparation information
    POST: Creates a new certificate with validation
    """
    if request.method == 'GET':
        try:
            # Use raw query to get all active certificates
            db = connection.get_db()
            certificates_collection = db.complete_certificates
            
            certificates = certificates_collection.find({})
            data = []
            
            for cert_doc in certificates:
                # Get sample preparation information
                request_info = {
                    'request_id': str(cert_doc.get('request_id', '')),
                    'request_no': 'Unknown',
                    'sample_lots_count': 0,
                    'total_specimens': 0,
                    'sample_lots': [],
                    'specimens': []
                }
                
                try:
                    # request_id is the ObjectId of the sample preparation
                    sample_prep_id = cert_doc.get('request_id')
                    if sample_prep_id:
                        # Use raw MongoDB query to find sample preparation
                        sample_prep_collection = db.sample_preparations
                        sample_prep_doc = sample_prep_collection.find_one({'_id': ObjectId(sample_prep_id)})
                        
                        if sample_prep_doc:
                            # Get detailed sample lots and specimens information
                            sample_lots_details = []
                            all_specimens = []
                            
                            for sample_lot in sample_prep_doc.get('sample_lots', []):
                                # Get sample lot information
                                sample_lot_obj = None
                                sample_lot_info = {
                                    'sample_lot_id': str(sample_lot.get('sample_lot_id', '')),
                                    'item_no': 'Unknown',
                                    'sample_type': 'Unknown',
                                    'material_type': 'Unknown',
                                    'job_id': 'Unknown'
                                }
                                
                                try:
                                    sample_lots_collection = db.sample_lots
                                    sample_lot_obj = sample_lots_collection.find_one({'_id': ObjectId(sample_lot.get('sample_lot_id'))})
                                    if sample_lot_obj:
                                        sample_lot_info.update({
                                            'item_no': sample_lot_obj.get('item_no', 'Unknown'),
                                            'sample_type': sample_lot_obj.get('sample_type', 'Unknown'),
                                            'material_type': sample_lot_obj.get('material_type', 'Unknown')
                                        })
                                        
                                        # Get job information
                                        try:
                                            jobs_collection = db.jobs
                                            job_obj = jobs_collection.find_one({'_id': sample_lot_obj.get('job_id')})
                                            if job_obj:
                                                sample_lot_info['job_id'] = job_obj.get('job_id', 'Unknown')
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                
                                # Get test method information
                                test_method_info = {
                                    'test_method_oid': str(sample_lot.get('test_method_oid', '')),
                                    'test_name': 'Unknown Method'
                                }
                                try:
                                    test_methods_collection = db.test_methods
                                    test_method_obj = test_methods_collection.find_one({'_id': ObjectId(sample_lot.get('test_method_oid'))})
                                    if test_method_obj:
                                        test_method_info['test_name'] = test_method_obj.get('test_name', 'Unknown Method')
                                except Exception:
                                    pass
                                
                                # Get specimens information for this sample lot
                                sample_lot_specimens = []
                                for specimen_oid in sample_lot.get('specimen_oids', []):
                                    specimen_info = {
                                        'specimen_oid': str(specimen_oid),
                                        'specimen_id': 'Unknown'
                                    }
                                    try:
                                        specimens_collection = db.specimens
                                        specimen_obj = specimens_collection.find_one({'_id': ObjectId(specimen_oid)})
                                        if specimen_obj:
                                            specimen_info['specimen_id'] = specimen_obj.get('specimen_id', 'Unknown')
                                    except Exception:
                                        pass
                                    
                                    sample_lot_specimens.append(specimen_info)
                                    all_specimens.append(specimen_info)
                                
                                sample_lots_details.append({
                                    'item_description': sample_lot.get('item_description', ''),
                                    'planned_test_date': sample_lot.get('planned_test_date'),
                                    'dimension_spec': sample_lot.get('dimension_spec'),
                                    'request_by': sample_lot.get('request_by'),
                                    'remarks': sample_lot.get('remarks'),
                                    'sample_lot_info': sample_lot_info,
                                    'test_method': test_method_info,
                                    'specimens': sample_lot_specimens,
                                    'specimens_count': len(sample_lot_specimens)
                                })
                            
                            request_info.update({
                                'request_no': sample_prep_doc.get('request_no', 'Unknown'),
                                'sample_lots_count': len(sample_prep_doc.get('sample_lots', [])),
                                'total_specimens': len(all_specimens),
                                'sample_lots': sample_lots_details,
                                'specimens': all_specimens
                            })
                except (DoesNotExist, Exception) as e:
                    print(f"Error fetching sample preparation: {e}")
                
                data.append({
                    'id': str(cert_doc.get('_id', '')),
                    'certificate_id': cert_doc.get('certificate_id', ''),
                    'date_of_sampling': cert_doc.get('date_of_sampling', ''),
                    'date_of_testing': cert_doc.get('date_of_testing', ''),
                    'issue_date': cert_doc.get('issue_date', ''),
                    'revision_no': cert_doc.get('revision_no', ''),
                    'customers_name_no': cert_doc.get('customers_name_no', ''),
                    'atten': cert_doc.get('atten', ''),
                    'customer_po': cert_doc.get('customer_po', ''),
                    'tested_by': cert_doc.get('tested_by', ''),
                    'reviewed_by': cert_doc.get('reviewed_by', ''),
                    'request_info': request_info,
                    'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else '',
                    'updated_at': cert_doc.get('updated_at').isoformat() if cert_doc.get('updated_at') else ''
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
            
            # Get database connection
            db = connection.get_db()
            
            # Auto-generate certificate_id if not provided
            if 'certificate_id' not in data or not data['certificate_id']:
                # Generate certificate_id automatically
                current_year = datetime.now().year
                year_prefix = f"CERT-{current_year}-"
                
                # Find the latest certificate_id for current year
                certificates_collection = db.complete_certificates
                
                # Query for certificates from current year, sorted by certificate_id descending
                latest_certificate = certificates_collection.find(
                    {'certificate_id': {'$regex': f'^{year_prefix}', '$options': 'i'}}
                ).sort('certificate_id', -1).limit(1)
                
                latest_certificate_list = list(latest_certificate)
                
                if latest_certificate_list:
                    # Extract sequence number from latest certificate
                    latest_certificate_id = latest_certificate_list[0]['certificate_id']
                    try:
                        # Extract the sequence number (last 4 digits)
                        sequence_part = latest_certificate_id.split('-')[-1]
                        next_sequence = int(sequence_part) + 1
                    except (ValueError, IndexError):
                        # If parsing fails, start from 1
                        next_sequence = 1
                else:
                    # No previous certificates for this year, start from 1
                    next_sequence = 1
                
                # Format sequence number with leading zeros (4 digits)
                formatted_sequence = str(next_sequence).zfill(4)
                generated_certificate_id = f"{year_prefix}{formatted_sequence}"
                
                # Check if generated certificate_id already exists (safety check)
                existing_check = certificates_collection.find_one({'certificate_id': generated_certificate_id})
                if existing_check:
                    # If somehow it exists, increment until we find available one
                    while existing_check:
                        next_sequence += 1
                        formatted_sequence = str(next_sequence).zfill(4)
                        generated_certificate_id = f"{year_prefix}{formatted_sequence}"
                        existing_check = certificates_collection.find_one({'certificate_id': generated_certificate_id})
                
                data['certificate_id'] = generated_certificate_id
            
            # Validate required fields (certificate_id is now auto-generated if not provided)
            required_fields = ['request_id']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate that the sample preparation request exists using raw MongoDB query
            try:
                request_id = ObjectId(data['request_id'])
                sample_prep_collection = db.sample_preparations
                sample_prep_doc = sample_prep_collection.find_one({'_id': request_id})
                if not sample_prep_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Sample preparation request with ID {data["request_id"]} not found'
                    }, status=404)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid sample preparation request ID format: {data["request_id"]}'
                }, status=400)
            
            certificate = Certificate(
                certificate_id=data['certificate_id'],
                date_of_sampling=data.get('date_of_sampling', ''),
                date_of_testing=data.get('date_of_testing', ''),
                issue_date=data.get('issue_date', ''),
                revision_no=data.get('revision_no', ''),
                customers_name_no=data.get('customers_name_no', ''),
                atten=data.get('atten', ''),
                customer_po=data.get('customer_po', ''),
                tested_by=data.get('tested_by', ''),
                reviewed_by=data.get('reviewed_by', ''),
                request_id=ObjectId(data['request_id'])
            )
            certificate.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificate created successfully',
                'data': {
                    'id': str(certificate.id),
                    'certificate_id': certificate.certificate_id,
                    'request_no': sample_prep_doc.get('request_no', 'Unknown'),
                    'customers_name_no': certificate.customers_name_no
                }
            }, status=201)
            
        except NotUniqueError:
            return JsonResponse({
                'status': 'error',
                'message': f'Certificate with certificate_id "{data.get("certificate_id", "")}" already exists. Certificate IDs must be unique.'
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
def certificate_detail(request, certificate_id):
    """
    Get, update, or delete a specific certificate by certificate_id
    GET: Returns certificate details with complete sample preparation information
    PUT: Updates certificate information
    DELETE: Deletes the certificate (soft delete)
    """
    try:
        # Use raw query to find certificate by certificate_id
        db = connection.get_db()
        certificates_collection = db.complete_certificates
        
        cert_doc = certificates_collection.find_one({'certificate_id': certificate_id})
        if not cert_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Certificate not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get detailed sample preparation information
            request_info = {
                'request_id': str(cert_doc.get('request_id', '')),
                'request_no': 'Unknown',
                'sample_lots_count': 0,
                'total_specimens': 0,
                'sample_lots': [],
                'specimens': []
            }
            
            try:
                # request_id is the ObjectId of the sample preparation
                sample_prep_id = cert_doc.get('request_id')
                if sample_prep_id:
                    # Use raw MongoDB query to find sample preparation
                    sample_prep_collection = db.sample_preparations
                    sample_prep_doc = sample_prep_collection.find_one({'_id': ObjectId(sample_prep_id)})
                    
                    if sample_prep_doc:
                        # Get detailed sample lots and specimens information
                        sample_lots_details = []
                        all_specimens = []
                        
                        for sample_lot in sample_prep_doc.get('sample_lots', []):
                            # Get sample lot information
                            sample_lot_obj = None
                            sample_lot_info = {
                                'sample_lot_id': str(sample_lot.get('sample_lot_id', '')),
                                'item_no': 'Unknown',
                                'sample_type': 'Unknown',
                                'material_type': 'Unknown',
                                'description': 'Unknown',
                                'job_id': 'Unknown',
                                'job_details': {}
                            }
                            
                            try:
                                sample_lots_collection = db.sample_lots
                                sample_lot_obj = sample_lots_collection.find_one({'_id': ObjectId(sample_lot.get('sample_lot_id'))})
                                if sample_lot_obj:
                                    sample_lot_info.update({
                                        'item_no': sample_lot_obj.get('item_no', 'Unknown'),
                                        'sample_type': sample_lot_obj.get('sample_type', 'Unknown'),
                                        'material_type': sample_lot_obj.get('material_type', 'Unknown'),
                                        'description': sample_lot_obj.get('description', 'Unknown')
                                    })
                                    
                                    # Get job information
                                    try:
                                        jobs_collection = db.jobs
                                        job_obj = jobs_collection.find_one({'_id': sample_lot_obj.get('job_id')})
                                        if job_obj:
                                            sample_lot_info['job_id'] = job_obj.get('job_id', 'Unknown')
                                            sample_lot_info['job_details'] = {
                                                'project_name': job_obj.get('project_name', ''),
                                                'end_user': job_obj.get('end_user', ''),
                                                'receive_date': job_obj.get('receive_date', '')
                                            }
                                    except Exception:
                                        pass
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
                                test_method_obj = test_methods_collection.find_one({'_id': ObjectId(sample_lot.get('test_method_oid'))})
                                if test_method_obj:
                                    test_method_info.update({
                                        'test_name': test_method_obj.get('test_name', 'Unknown Method'),
                                        'test_description': test_method_obj.get('test_description', 'Unknown'),
                                        'test_columns': test_method_obj.get('test_columns', []),
                                        'hasImage': test_method_obj.get('hasImage', False)
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
                                    specimen_obj = specimens_collection.find_one({'_id': ObjectId(specimen_oid)})
                                    if specimen_obj:
                                        specimen_info.update({
                                            'specimen_id': specimen_obj.get('specimen_id', 'Unknown'),
                                            'created_at': specimen_obj.get('created_at').isoformat() if specimen_obj.get('created_at') else '',
                                            'updated_at': specimen_obj.get('updated_at').isoformat() if specimen_obj.get('updated_at') else ''
                                        })
                                except Exception:
                                    pass
                                
                                sample_lot_specimens.append(specimen_info)
                                all_specimens.append(specimen_info)
                            
                            sample_lots_details.append({
                                'item_description': sample_lot.get('item_description', ''),
                                'planned_test_date': sample_lot.get('planned_test_date'),
                                'dimension_spec': sample_lot.get('dimension_spec'),
                                'request_by': sample_lot.get('request_by'),
                                'remarks': sample_lot.get('remarks'),
                                'sample_lot_info': sample_lot_info,
                                'test_method': test_method_info,
                                'specimens': sample_lot_specimens,
                                'specimens_count': len(sample_lot_specimens)
                            })
                        
                        request_info.update({
                            'request_no': sample_prep_doc.get('request_no', 'Unknown'),
                            'sample_lots_count': len(sample_prep_doc.get('sample_lots', [])),
                            'total_specimens': len(all_specimens),
                            'sample_lots': sample_lots_details,
                            'specimens': all_specimens,
                            'created_at': sample_prep_doc.get('created_at').isoformat() if sample_prep_doc.get('created_at') else '',
                            'updated_at': sample_prep_doc.get('updated_at').isoformat() if sample_prep_doc.get('updated_at') else ''
                        })
            except (DoesNotExist, Exception) as e:
                print(f"Error fetching sample preparation: {e}")
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(cert_doc.get('_id', '')),
                    'certificate_id': cert_doc.get('certificate_id', ''),
                    'date_of_sampling': cert_doc.get('date_of_sampling', ''),
                    'date_of_testing': cert_doc.get('date_of_testing', ''),
                    'issue_date': cert_doc.get('issue_date', ''),
                    'revision_no': cert_doc.get('revision_no', ''),
                    'customers_name_no': cert_doc.get('customers_name_no', ''),
                    'atten': cert_doc.get('atten', ''),
                    'customer_po': cert_doc.get('customer_po', ''),
                    'tested_by': cert_doc.get('tested_by', ''),
                    'reviewed_by': cert_doc.get('reviewed_by', ''),
                    'request_info': request_info,
                    'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else '',
                    'updated_at': cert_doc.get('updated_at').isoformat() if cert_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update fields if provided (excluding certificate_id and request_id for integrity)
                update_fields = ['date_of_sampling', 'date_of_testing', 'issue_date', 'revision_no',
                               'customers_name_no', 'atten', 'customer_po', 'tested_by', 'reviewed_by']
                for field in update_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                if len(update_doc) <= 1:  # Only timestamp was added
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes provided'
                    }, status=400)
                
                # Update the document
                result = certificates_collection.update_one(
                    {'certificate_id': certificate_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated certificate document
                updated_cert = certificates_collection.find_one({'certificate_id': certificate_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Certificate updated successfully',
                    'data': {
                        'id': str(updated_cert.get('_id', '')),
                        'certificate_id': updated_cert.get('certificate_id', ''),
                        'customers_name_no': updated_cert.get('customers_name_no', ''),
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
                {'certificate_id': certificate_id}
            )
            
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Certificate not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificate deleted successfully',
                'data': {
                    'certificate_id': certificate_id,
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
def certificate_search(request):
    """
    Search certificates by various criteria
    Query parameters:
    - certificate_id: Search by certificate ID (partial match)
    - customers_name_no: Search by customer name/number (partial match)
    - tested_by: Search by tester name (partial match)
    - issue_date: Search by issue date (exact match)
    """
    try:
        # Get query parameters
        cert_id = request.GET.get('certificate_id', '')
        customer = request.GET.get('customers_name_no', '')
        tester = request.GET.get('tested_by', '')
        issue_date = request.GET.get('issue_date', '')
        
        # Build query for raw MongoDB
        query = {}
        if cert_id:
            query['certificate_id'] = {'$regex': cert_id, '$options': 'i'}
        if customer:
            query['customers_name_no'] = {'$regex': customer, '$options': 'i'}
        if tester:
            query['tested_by'] = {'$regex': tester, '$options': 'i'}
        if issue_date:
            query['issue_date'] = issue_date
        
        # Use raw query to search
        db = connection.get_db()
        certificates_collection = db.complete_certificates
        
        certificates = certificates_collection.find(query)
        
        data = []
        for cert_doc in certificates:
            # Get basic sample preparation info
            request_no = 'Unknown'
            try:
                # request_id is the ObjectId of the sample preparation
                sample_prep_id = cert_doc.get('request_id')
                if sample_prep_id:
                    # Use raw MongoDB query to find sample preparation
                    sample_prep_collection = db.sample_preparations
                    sample_prep_doc = sample_prep_collection.find_one({'_id': ObjectId(sample_prep_id)})
                    
                    if sample_prep_doc:
                        request_no = sample_prep_doc.get('request_no', 'Unknown')
            except (DoesNotExist, Exception):
                pass
            
            data.append({
                'id': str(cert_doc.get('_id', '')),
                'certificate_id': cert_doc.get('certificate_id', ''),
                'customers_name_no': cert_doc.get('customers_name_no', ''),
                'issue_date': cert_doc.get('issue_date', ''),
                'tested_by': cert_doc.get('tested_by', ''),
                'reviewed_by': cert_doc.get('reviewed_by', ''),
                'request_no': request_no,
                'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'certificate_id': cert_id,
                'customers_name_no': customer,
                'tested_by': tester,
                'issue_date': issue_date
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def certificate_stats(request):
    """
    Get certificate statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        certificates_collection = db.complete_certificates
        
        total_certificates = certificates_collection.count_documents({})
        
        # Count by month of issue
        monthly_stats = certificates_collection.aggregate([
            {'$match': {'issue_date': {'$ne': ''}}},
            {
                '$addFields': {
                    'issue_year_month': {
                        '$substr': ['$issue_date', 0, 7]  # Extract YYYY-MM
                    }
                }
            },
            {
                '$group': {
                    '_id': '$issue_year_month',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': -1}}
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
                'monthly_issue_stats': list(monthly_stats),
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
def certificate_by_request(request, request_no):
    """
    Get certificates for a specific sample preparation request
    """
    try:
        # First find the sample preparation by request_no using raw MongoDB query
        db = connection.get_db()
        sample_prep_collection = db.sample_preparations
        sample_prep_doc = sample_prep_collection.find_one({'request_no': request_no})
        
        if not sample_prep_doc:
            return JsonResponse({
                'status': 'error',
                'message': f'Sample preparation request "{request_no}" not found'
            }, status=404)
        
        sample_prep_id = sample_prep_doc.get('_id')
        
        # Use raw query to find certificates by request_id (sample preparation ObjectId)
        certificates_collection = db.complete_certificates
        
        certificates = certificates_collection.find({
            'request_id': sample_prep_id
        })
        
        data = []
        for cert_doc in certificates:
            data.append({
                'id': str(cert_doc.get('_id', '')),
                'certificate_id': cert_doc.get('certificate_id', ''),
                'issue_date': cert_doc.get('issue_date', ''),
                'customers_name_no': cert_doc.get('customers_name_no', ''),
                'tested_by': cert_doc.get('tested_by', ''),
                'reviewed_by': cert_doc.get('reviewed_by', ''),
                'created_at': cert_doc.get('created_at').isoformat() if cert_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'request_info': {
                'request_no': sample_prep_doc.get('request_no', ''),
                'sample_lots_count': len(sample_prep_doc.get('sample_lots', [])),
                'total_specimens': sum(len(sl.get('specimen_oids', [])) for sl in sample_prep_doc.get('sample_lots', []))
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
