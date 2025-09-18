from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from .models import CertificateItem, SpecimenSection, ImageInfo
from certificates.models import Certificate
from specimens.models import Specimen
from samplepreperation.models import SamplePreparation


# ============= CERTIFICATE ITEMS CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
def certificate_item_list(request):
    """
    List all certificate items or create a new certificate item
    GET: Returns list of all certificate items with related data
    POST: Creates a new certificate item with validation
    """
    if request.method == 'GET':
        try:
            # Use raw query to get all certificate items
            db = connection.get_db()
            certificate_items_collection = db.certificate_items
            
            # Apply filters if provided
            query = {'is_active': True}
            
            # Filter by certificate_id if provided
            certificate_id = request.GET.get('certificate_id')
            if certificate_id:
                query['certificate_id'] = certificate_id
            
            # Filter by material_grade if provided
            material_grade = request.GET.get('material_grade')
            if material_grade:
                query['material_grade'] = {'$regex': material_grade, '$options': 'i'}
            
            certificate_items = certificate_items_collection.find(query).sort('created_at', -1)
            data = []
            
            for item_doc in certificate_items:
                # Process specimen sections with enhanced data
                specimen_sections_data = []
                total_specimens = 0
                
                for section in item_doc.get('specimen_sections', []):
                    # Get specimen information
                    specimen_info = {
                        'specimen_id': str(section.get('specimen_id', '')),
                        'specimen_name': 'Unknown'
                    }
                    try:
                        specimens_collection = db.specimens
                        specimen_doc = specimens_collection.find_one({'_id': ObjectId(section.get('specimen_id'))})
                        if specimen_doc:
                            specimen_info['specimen_name'] = specimen_doc.get('specimen_id', 'Unknown')
                    except Exception:
                        pass
                    
                    # Parse test results for summary
                    test_results_summary = []
                    try:
                        import json as json_parser
                        test_results = json_parser.loads(section.get('test_results', '[]'))
                        for result in test_results:
                            if isinstance(result, dict) and 'data' in result:
                                data_keys = list(result['data'].keys())
                                test_results_summary.append({
                                    'sample_id': result['data'].get('Sample ID', 'Unknown'),
                                    'test_parameters': data_keys[:5]  # First 5 parameters
                                })
                    except Exception:
                        test_results_summary = [{'sample_id': 'Parse Error', 'test_parameters': []}]
                    
                    specimen_sections_data.append({
                        'specimen_info': specimen_info,
                        'test_results_count': len(test_results_summary),
                        'test_results_summary': test_results_summary,
                        'images_count': len(section.get('images_list', []))
                    })
                    total_specimens += 1
                
                # Get certificate information
                certificate_info = {
                    'certificate_id': str(item_doc.get('certificate_id', '')),
                    'issue_date': 'Unknown',
                    'customers_name_no': 'Unknown'
                }
                try:
                    # Try to find certificate by ObjectId
                    db_certificates = db.complete_certificates
                    cert_doc = db_certificates.find_one({'_id': item_doc.get('certificate_id')})
                    if cert_doc:
                        certificate_info.update({
                            'certificate_id': cert_doc.get('certificate_id', 'Unknown'),
                            'issue_date': cert_doc.get('issue_date', 'Unknown'),
                            'customers_name_no': cert_doc.get('customers_name_no', 'Unknown')
                        })
                except Exception:
                    pass
                
                data.append({
                    'id': str(item_doc.get('_id', '')),
                    'certificate_id': str(item_doc.get('certificate_id', '')),
                    'certificate_info': certificate_info,
                    'sample_preparation_method': item_doc.get('sample_preparation_method', ''),
                    'material_grade': item_doc.get('material_grade', ''),
                    'temperature': item_doc.get('temperature', ''),
                    'humidity': item_doc.get('humidity', ''),
                    'specimen_sections': specimen_sections_data,
                    'total_specimens': total_specimens,
                    'comments': item_doc.get('comments', ''),
                    'created_at': item_doc.get('created_at').isoformat() if item_doc.get('created_at') else '',
                    'updated_at': item_doc.get('updated_at').isoformat() if item_doc.get('updated_at') else ''
                })
            
            return JsonResponse({
                'status': 'success',
                'data': data,
                'total': len(data),
                'filters_applied': {
                    'certificate_id': certificate_id,
                    'material_grade': material_grade
                }
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
            required_fields = ['certificate_id', 'specimen_sections']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Validate certificate exists using ObjectId
            try:
                certificate_oid = ObjectId(data['certificate_id'])
                db = connection.get_db()
                certificates_collection = db.complete_certificates
                certificate_doc = certificates_collection.find_one({'_id': certificate_oid})
                if not certificate_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Certificate with ID {data["certificate_id"]} not found'
                    }, status=404)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid certificate ID format: {data["certificate_id"]}'
                }, status=400)
            
            # Validate specimen_sections is an array
            if not isinstance(data['specimen_sections'], list) or len(data['specimen_sections']) == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'specimen_sections must be a non-empty array'
                }, status=400)
            
            # Process and validate each specimen section
            validated_specimen_sections = []
            for i, section_data in enumerate(data['specimen_sections']):
                # Validate required fields for each specimen section
                section_required = ['test_results', 'specimen_id']
                for field in section_required:
                    if field not in section_data or not section_data[field]:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Required field "{field}" is missing in specimen_sections[{i}]'
                        }, status=400)
                
                # Validate specimen exists using raw MongoDB query
                try:
                    specimen_oid = ObjectId(section_data['specimen_id'])
                    specimens_collection = db.specimens
                    specimen_doc = specimens_collection.find_one({'_id': specimen_oid})
                    if not specimen_doc:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Specimen with ID {section_data["specimen_id"]} not found in specimen_sections[{i}]'
                        }, status=404)
                except Exception:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Invalid specimen ID format: {section_data["specimen_id"]} in specimen_sections[{i}]'
                    }, status=400)
                
                # Validate test_results is valid JSON
                try:
                    json.loads(section_data['test_results'])
                except json.JSONDecodeError:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'test_results must be valid JSON in specimen_sections[{i}]'
                    }, status=400)
                
                # Process images_list if provided
                images_list = []
                if 'images_list' in section_data and isinstance(section_data['images_list'], list):
                    for j, image_data in enumerate(section_data['images_list']):
                        if isinstance(image_data, dict):
                            image_info = ImageInfo(
                                image_url=image_data.get('image_url', ''),
                                caption=image_data.get('caption', '')
                            )
                            images_list.append(image_info)
                
                # Create validated specimen section
                specimen_section = SpecimenSection(
                    test_results=section_data['test_results'],
                    images_list=images_list,
                    specimen_id=ObjectId(section_data['specimen_id']),
                    equipment_name=section_data.get('equipment_name', ''),
                    equipment_calibration=section_data.get('equipment_calibration', '')
                )
                validated_specimen_sections.append(specimen_section)
            
            # Create certificate item
            certificate_item = CertificateItem(
                certificate_id=certificate_oid,
                sample_preparation_method=data.get('sample_preparation_method', ''),
                material_grade=data.get('material_grade', ''),
                temperature=data.get('temperature', ''),
                humidity=data.get('humidity', ''),
                po=data.get('po', ''),
                mtc_no=data.get('mtc_no', ''),
                heat_no=data.get('heat_no', ''),
                comments=data.get('comments', ''),
                specimen_sections=validated_specimen_sections
            )
            certificate_item.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificate item created successfully',
                'data': {
                    'id': str(certificate_item.id),
                    'certificate_id': str(certificate_item.certificate_id),
                    'specimen_sections_count': len(certificate_item.specimen_sections),
                    'material_grade': certificate_item.material_grade
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
def certificate_item_detail(request, item_id):
    """
    Get, update, or delete a specific certificate item by ID
    GET: Returns certificate item details with complete relationship data
    PUT: Updates certificate item
    DELETE: Soft deletes the certificate item
    """
    try:
        # Use raw query to find certificate item by ID
        db = connection.get_db()
        certificate_items_collection = db.certificate_items
        
        try:
            item_doc = certificate_items_collection.find_one({
                '_id': ObjectId(item_id),
                'is_active': True
            })
        except Exception:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid certificate item ID format'
            }, status=400)
        
        if not item_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Certificate item not found'
            }, status=404)
        
        if request.method == 'GET':
            # Process specimen sections with detailed relationship data
            specimen_sections_data = []
            for section in item_doc.get('specimen_sections', []):
                # Get detailed specimen information
                specimen_info = {
                    'specimen_id': str(section.get('specimen_id', '')),
                    'specimen_name': 'Unknown'
                }
                try:
                    specimens_collection = db.specimens
                    specimen_doc = specimens_collection.find_one({'_id': ObjectId(section.get('specimen_id'))})
                    if specimen_doc:
                        specimen_info['specimen_name'] = specimen_doc.get('specimen_id', 'Unknown')
                except Exception:
                    pass
                
                # Parse and structure test results
                test_results_data = []
                try:
                    import json as json_parser
                    test_results = json_parser.loads(section.get('test_results', '[]'))
                    test_results_data = test_results
                except Exception:
                    test_results_data = []
                
                # Process images list
                images_data = []
                for image in section.get('images_list', []):
                    images_data.append({
                        'image_url': image.get('image_url', ''),
                        'caption': image.get('caption', '')
                    })
                
                specimen_sections_data.append({
                    'specimen_id': str(section.get('specimen_id', '')),
                    'specimen_info': specimen_info,
                    'test_results': test_results_data,
                    'test_results_summary': test_results_data,  # For compatibility
                    'images_list': images_data,
                    'equipment_name': section.get('equipment_name', ''),
                    'equipment_calibration': section.get('equipment_calibration', '')
                })
            
            # Get certificate information
            certificate_info = {
                'certificate_id': str(item_doc.get('certificate_id', '')),
                'issue_date': 'Unknown',
                'customers_name_no': 'Unknown',
                'date_of_sampling': 'Unknown',
                'date_of_testing': 'Unknown'
            }
            try:
                db_certificates = db.complete_certificates
                cert_doc = db_certificates.find_one({'_id': item_doc.get('certificate_id')})
                if cert_doc:
                    certificate_info.update({
                        'issue_date': cert_doc.get('issue_date', 'Unknown'),
                        'customers_name_no': cert_doc.get('customers_name_no', 'Unknown'),
                        'date_of_sampling': cert_doc.get('date_of_sampling', 'Unknown'),
                        'date_of_testing': cert_doc.get('date_of_testing', 'Unknown')
                    })
            except Exception:
                pass
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(item_doc.get('_id', '')),
                    'certificate_id': str(item_doc.get('certificate_id', '')),
                    'certificate_info': certificate_info,
                    'sample_preparation_method': item_doc.get('sample_preparation_method', ''),
                    'material_grade': item_doc.get('material_grade', ''),
                    'temperature': item_doc.get('temperature', ''),
                    'humidity': item_doc.get('humidity', ''),
                    'po': item_doc.get('po', ''),
                    'mtc_no': item_doc.get('mtc_no', ''),
                    'heat_no': item_doc.get('heat_no', ''),
                    'comments': item_doc.get('comments', ''),
                    'specimen_sections': specimen_sections_data,
                    'total_specimens': len(specimen_sections_data),
                    'created_at': item_doc.get('created_at').isoformat() if item_doc.get('created_at') else '',
                    'updated_at': item_doc.get('updated_at').isoformat() if item_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                update_doc = {}
                
                # Update basic fields if provided
                updateable_fields = [
                    'sample_preparation_method', 'material_grade', 'temperature', 
                    'humidity', 'po', 'mtc_no', 'heat_no', 'comments'
                ]
                for field in updateable_fields:
                    if field in data:
                        update_doc[field] = data[field]
                
                # Update certificate_id if provided and validate
                if 'certificate_id' in data:
                    new_certificate_id = data['certificate_id']
                    try:
                        db_certificates = db.complete_certificates
                        certificate_doc = db_certificates.find_one({'_id': ObjectId(new_certificate_id)})
                        if not certificate_doc:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Certificate with ID {new_certificate_id} not found'
                            }, status=404)
                        update_doc['certificate_id'] = new_certificate_id
                    except Exception:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Error validating certificate'
                        }, status=400)
                
                # For specimen_sections update, we need more complex handling
                if 'specimen_sections' in data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Updating specimen_sections is complex. Please use DELETE and CREATE for specimen section changes.'
                    }, status=400)
                
                update_doc['updated_at'] = datetime.now()
                
                if len(update_doc) <= 1:  # Only timestamp was added
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes provided'
                    }, status=400)
                
                # Update the document
                result = certificate_items_collection.update_one(
                    {'_id': ObjectId(item_id), 'is_active': True},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made or certificate item not found'
                    }, status=400)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Certificate item updated successfully',
                    'data': {
                        'id': item_id,
                        'updated_at': update_doc['updated_at'].isoformat()
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, status=400)
        
        elif request.method == 'DELETE':
            # Soft delete by setting is_active to False
            result = certificate_items_collection.update_one(
                {'_id': ObjectId(item_id), 'is_active': True},
                {'$set': {'is_active': False, 'updated_at': datetime.now()}}
            )
            
            if result.modified_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Certificate item not found or already deleted'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Certificate item deleted successfully',
                'data': {
                    'id': item_id,
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
def certificate_item_search(request):
    """
    Search certificate items by various criteria
    Query parameters:
    - certificate_id: Search by certificate ID (exact match)
    - material_grade: Search by material grade (partial match)
    - equipment_name: Search by equipment name (partial match)
    - specimen_id: Search by specimen ID (exact match)
    """
    try:
        # Get query parameters
        certificate_id_query = request.GET.get('certificate_id', '')
        material_grade_query = request.GET.get('material_grade', '')
        specimen_id_query = request.GET.get('specimen_id', '')
        
        # Build query for raw MongoDB
        query = {'is_active': True}
        
        if certificate_id_query:
            try:
                query['certificate_id'] = ObjectId(certificate_id_query)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid certificate ID format: {certificate_id_query}'
                }, status=400)
        if material_grade_query:
            query['material_grade'] = {'$regex': material_grade_query, '$options': 'i'}
        if specimen_id_query:
            try:
                query['specimen_sections.specimen_id'] = ObjectId(specimen_id_query)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid specimen_id format'
                }, status=400)
        
        # Use raw query to search
        db = connection.get_db()
        certificate_items_collection = db.certificate_items
        
        certificate_items = certificate_items_collection.find(query).sort('created_at', -1)
        
        data = []
        for item_doc in certificate_items:
            specimen_count = len(item_doc.get('specimen_sections', []))
            
            data.append({
                'id': str(item_doc.get('_id', '')),
                'certificate_id': str(item_doc.get('certificate_id', '')),
                'material_grade': item_doc.get('material_grade', ''),
                'specimen_count': specimen_count,
                'created_at': item_doc.get('created_at').isoformat() if item_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'certificate_id': certificate_id_query,
                'material_grade': material_grade_query,
                'specimen_id': specimen_id_query
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def certificate_item_by_certificate(request, certificate_id):
    """
    Get all certificate items for a specific certificate
    """
    try:
        # Use raw query to find all certificate items for this certificate
        db = connection.get_db()
        certificate_items_collection = db.certificate_items
        
        query = {
            'certificate_id': certificate_id,
            'is_active': True
        }
        
        certificate_items = certificate_items_collection.find(query).sort('created_at', -1)
        data = []
        
        for item_doc in certificate_items:
            # Count specimens and images
            specimen_count = len(item_doc.get('specimen_sections', []))
            total_images = sum(len(section.get('images_list', [])) for section in item_doc.get('specimen_sections', []))
            
            data.append({
                'id': str(item_doc.get('_id', '')),
                'certificate_id': str(item_doc.get('certificate_id', '')),
                'material_grade': item_doc.get('material_grade', ''),
                'specimen_count': specimen_count,
                'images_count': total_images,
                'comments': item_doc.get('comments', ''),
                'created_at': item_doc.get('created_at').isoformat() if item_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'certificate_id': certificate_id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def certificate_item_stats(request):
    """
    Get certificate item statistics
    """
    try:
        # Use raw query for statistics
        db = connection.get_db()
        certificate_items_collection = db.certificate_items
        
        total_items = certificate_items_collection.count_documents({'is_active': True})
        
        # Calculate statistics using aggregation
        pipeline = [
            {'$match': {'is_active': True}},
            {
                '$project': {
                    'certificate_id': 1,
                    'material_grade': 1,
                    'specimen_count': {'$size': '$specimen_sections'},
                    'images_count': {
                        '$sum': {
                            '$map': {
                                'input': '$specimen_sections',
                                'as': 'section',
                                'in': {'$size': '$$section.images_list'}
                            }
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_specimens': {'$sum': '$specimen_count'},
                    'total_images': {'$sum': '$images_count'},
                    'avg_specimens_per_item': {'$avg': '$specimen_count'},
                    'unique_certificates': {'$addToSet': '$certificate_id'},
                    'unique_materials': {'$addToSet': '$material_grade'}
                }
            }
        ]
        
        stats_result = list(certificate_items_collection.aggregate(pipeline))
        stats = stats_result[0] if stats_result else {
            'total_specimens': 0,
            'total_images': 0,
            'avg_specimens_per_item': 0,
            'unique_certificates': [],
            'unique_materials': []
        }
        
        # Material grade distribution
        material_pipeline = [
            {'$match': {'is_active': True, 'material_grade': {'$ne': '', '$exists': True}}},
            {'$group': {'_id': '$material_grade', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        material_stats = list(certificate_items_collection.aggregate(material_pipeline))
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_certificate_items': total_items,
                'total_specimens_tested': stats.get('total_specimens', 0),
                'total_images_attached': stats.get('total_images', 0),
                'avg_specimens_per_item': round(stats.get('avg_specimens_per_item', 0), 2),
                'unique_certificates_count': len(stats.get('unique_certificates', [])),
                'unique_materials_count': len(stats.get('unique_materials', [])),
                'top_materials': material_stats
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)