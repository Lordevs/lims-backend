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
            certificates_collection = db.certificates
            
            certificates = certificates_collection.find({'is_active': True})
            data = []
            
            for cert_doc in certificates:
                # Get sample preparation information
                request_info = {
                    'request_id': str(cert_doc.get('request_id', '')),
                    'request_no': 'Unknown',
                    'sample_lots_count': 0,
                    'total_specimens': 0
                }
                
                try:
                    sample_prep = SamplePreparation.objects.get(id=ObjectId(cert_doc.get('request_id')))
                    request_info.update({
                        'request_no': sample_prep.request_no,
                        'sample_lots_count': len(sample_prep.sample_lots),
                        'total_specimens': sum(len(sl.specimen_oids) for sl in sample_prep.sample_lots)
                    })
                except (DoesNotExist, Exception):
                    pass
                
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
            
            # Validate required fields
            required_fields = ['certificate_id', 'request_id']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate that the sample preparation request exists
            try:
                sample_prep = SamplePreparation.objects.get(id=ObjectId(data['request_id']))
            except (DoesNotExist, Exception):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Sample preparation request with ID {data["request_id"]} not found'
                }, status=404)
            
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
                    'request_no': sample_prep.request_no,
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
        certificates_collection = db.certificates
        
        cert_doc = certificates_collection.find_one({'certificate_id': certificate_id, 'is_active': True})
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
                'sample_lots_summary': []
            }
            
            try:
                sample_prep = SamplePreparation.objects.get(id=ObjectId(cert_doc.get('request_id')))
                
                # Get sample lots summary
                sample_lots_summary = []
                for sample_lot in sample_prep.sample_lots:
                    sample_lots_summary.append({
                        'item_description': sample_lot.item_description,
                        'planned_test_date': sample_lot.planned_test_date,
                        'request_by': sample_lot.request_by,
                        'specimens_count': len(sample_lot.specimen_oids)
                    })
                
                request_info.update({
                    'request_no': sample_prep.request_no,
                    'sample_lots_count': len(sample_prep.sample_lots),
                    'total_specimens': sum(len(sl.specimen_oids) for sl in sample_prep.sample_lots),
                    'sample_lots_summary': sample_lots_summary,
                    'created_at': sample_prep.created_at.isoformat() if sample_prep.created_at else '',
                    'updated_at': sample_prep.updated_at.isoformat() if sample_prep.updated_at else ''
                })
            except (DoesNotExist, Exception):
                pass
            
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
                    {'certificate_id': certificate_id, 'is_active': True},
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
            # Soft delete by setting is_active to False
            result = certificates_collection.update_one(
                {'certificate_id': certificate_id, 'is_active': True},
                {'$set': {'is_active': False, 'updated_at': datetime.now()}}
            )
            
            if result.modified_count == 0:
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
        query = {'is_active': True}
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
        certificates_collection = db.certificates
        
        certificates = certificates_collection.find(query)
        
        data = []
        for cert_doc in certificates:
            # Get basic sample preparation info
            request_no = 'Unknown'
            try:
                sample_prep = SamplePreparation.objects.get(id=ObjectId(cert_doc.get('request_id')))
                request_no = sample_prep.request_no
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
        certificates_collection = db.certificates
        
        total_certificates = certificates_collection.count_documents({'is_active': True})
        
        # Count by month of issue
        monthly_stats = certificates_collection.aggregate([
            {'$match': {'is_active': True, 'issue_date': {'$ne': ''}}},
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
            {'$match': {'is_active': True, 'tested_by': {'$ne': ''}}},
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
        # First find the sample preparation by request_no
        try:
            sample_prep = SamplePreparation.objects.get(request_no=request_no)
        except DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Sample preparation request "{request_no}" not found'
            }, status=404)
        
        # Use raw query to find certificates by request_id
        db = connection.get_db()
        certificates_collection = db.certificates
        
        certificates = certificates_collection.find({
            'request_id': sample_prep.id,
            'is_active': True
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
                'request_no': sample_prep.request_no,
                'sample_lots_count': len(sample_prep.sample_lots),
                'total_specimens': sum(len(sl.specimen_oids) for sl in sample_prep.sample_lots)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
