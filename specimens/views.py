from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from mongoengine import connection
from mongoengine.errors import DoesNotExist, ValidationError, NotUniqueError

from .models import Specimen
from authentication.decorators import any_authenticated_user
import os
import shutil
from django.conf import settings


# ============= UTILITY FUNCTIONS =============

def delete_specimen_media_folder(specimen_oid):
    """
    Delete the media folder for a specific specimen
    Args:
        specimen_oid: ObjectId of the specimen
    Returns:
        tuple: (success, message)
    """
    try:
        # Convert ObjectId to string
        specimen_id_str = str(specimen_oid)
        
        # Create the media folder path
        media_folder_path = os.path.join(settings.MEDIA_ROOT, 'certificate_images', specimen_id_str)
        
        # Check if folder exists
        if os.path.exists(media_folder_path):
            # Delete the entire folder and its contents
            shutil.rmtree(media_folder_path)
            return True, f"Media folder deleted: {media_folder_path}"
        else:
            return True, f"No media folder found for specimen: {specimen_id_str}"
            
    except Exception as e:
        return False, f"Error deleting media folder: {str(e)}"


# ============= SPECIMEN CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def specimen_list(request):
    """
    List all specimens or create a new specimen
    GET: Returns list of all specimens
    POST: Creates a new specimen (specimen_id must be unique)
    """
    if request.method == 'GET':
        try:
            # Use raw query to get all specimens
            db = connection.get_db()
            specimens_collection = db.specimens
            
            specimens = specimens_collection.find({})
            data = []
            
            for specimen_doc in specimens:
                data.append({
                    'id': str(specimen_doc.get('_id', '')),
                    'specimen_id': specimen_doc.get('specimen_id', ''),
                    'created_at': specimen_doc.get('created_at').isoformat() if specimen_doc.get('created_at') else '',
                    'updated_at': specimen_doc.get('updated_at').isoformat() if specimen_doc.get('updated_at') else ''
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
            if 'specimen_id' not in data or not data['specimen_id']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Required field "specimen_id" is missing or empty'
                }, status=400)
            
            # Check if specimen_id already exists (ensure uniqueness)
            db = connection.get_db()
            specimens_collection = db.specimens
            existing_specimen = specimens_collection.find_one({'specimen_id': data['specimen_id']})
            
            if existing_specimen:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Specimen with ID "{data["specimen_id"]}" already exists. Specimen IDs must be unique.'
                }, status=400)
            
            specimen = Specimen(
                specimen_id=data['specimen_id']
            )
            specimen.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Specimen created successfully',
                'data': {
                    'id': str(specimen.id),
                    'specimen_id': specimen.specimen_id,
                    'created_at': specimen.created_at.isoformat()
                }
            }, status=201)
            
        except NotUniqueError:
            return JsonResponse({
                'status': 'error',
                'message': f'Specimen with ID "{data.get("specimen_id", "")}" already exists. Specimen IDs must be unique.'
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
def specimen_detail(request, object_id):
    """
    Get, update, or delete a specific specimen by ObjectId
    GET: Returns specimen details
    PUT: Partial update of specimen (can update specimen_id, must be unique)
    DELETE: Deletes the specimen
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
        
        # Use raw query to find specimen by ObjectId
        db = connection.get_db()
        specimens_collection = db.specimens
        
        specimen_doc = specimens_collection.find_one({'_id': obj_id})
        if not specimen_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Specimen not found'
            }, status=404)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(specimen_doc.get('_id', '')),
                    'specimen_id': specimen_doc.get('specimen_id', ''),
                    'created_at': specimen_doc.get('created_at').isoformat() if specimen_doc.get('created_at') else '',
                    'updated_at': specimen_doc.get('updated_at').isoformat() if specimen_doc.get('updated_at') else ''
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
                
                # Prepare update document
                update_doc = {}
                
                # Update specimen_id if provided
                if 'specimen_id' in data:
                    new_specimen_id = data['specimen_id']
                    
                    # Validate specimen_id is not empty
                    if not new_specimen_id:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'specimen_id cannot be empty'
                        }, status=400)
                    
                    # Check if new specimen_id is different from current
                    current_specimen_id = specimen_doc.get('specimen_id')
                    if new_specimen_id != current_specimen_id:
                        # Check if new specimen_id already exists
                        existing_specimen = specimens_collection.find_one({
                            'specimen_id': new_specimen_id,
                            '_id': {'$ne': obj_id}  # Exclude current document
                        })
                        if existing_specimen:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Specimen with ID "{new_specimen_id}" already exists. Specimen IDs must be unique.'
                            }, status=400)
                        
                        update_doc['specimen_id'] = new_specimen_id
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Check if there are any actual changes
                if len(update_doc) == 1:  # Only timestamp was added
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes provided'
                    }, status=400)
                
                # Update the document
                result = specimens_collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated specimen document
                updated_specimen = specimens_collection.find_one({'_id': obj_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Specimen updated successfully',
                    'data': {
                        'id': str(updated_specimen.get('_id', '')),
                        'specimen_id': updated_specimen.get('specimen_id', ''),
                        'created_at': updated_specimen.get('created_at').isoformat() if updated_specimen.get('created_at') else '',
                        'updated_at': updated_specimen.get('updated_at').isoformat() if updated_specimen.get('updated_at') else ''
                    }
                })
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, status=400)
        
        elif request.method == 'DELETE':
            # Delete the specimen's media folder first
            media_success, media_message = delete_specimen_media_folder(obj_id)
            
            # Delete the specimen from database
            result = specimens_collection.delete_one({'_id': obj_id})
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Specimen not found'
                }, status=404)
            
            # Prepare response data
            response_data = {
                'id': str(obj_id),
                'specimen_id': specimen_doc.get('specimen_id', ''),
                'deleted_at': datetime.now().isoformat(),
                'media_cleanup': {
                    'success': media_success,
                    'message': media_message
                }
            }
            
            return JsonResponse({
                'status': 'success',
                'message': 'Specimen deleted successfully',
                'data': response_data
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@any_authenticated_user
def specimen_search(request):
    """
    Search specimens by specimen_id (partial match)
    Query parameters:
    - specimen_id: Search by specimen_id (case-insensitive partial match)
    """
    try:
        # Get query parameters
        specimen_id_query = request.GET.get('specimen_id', '')
        
        # Build query for raw MongoDB
        query = {}
        if specimen_id_query:
            query['specimen_id'] = {'$regex': specimen_id_query, '$options': 'i'}
        
        # Use raw query to search
        db = connection.get_db()
        specimens_collection = db.specimens
        
        specimens = specimens_collection.find(query)
        
        data = []
        for specimen_doc in specimens:
            data.append({
                'id': str(specimen_doc.get('_id', '')),
                'specimen_id': specimen_doc.get('specimen_id', ''),
                'created_at': specimen_doc.get('created_at').isoformat() if specimen_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
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
@any_authenticated_user
def specimen_stats(request):
    """
    Get specimen statistics
    """
    try:
        # Use raw query to count specimens
        db = connection.get_db()
        specimens_collection = db.specimens
        
        total_specimens = specimens_collection.count_documents({})
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_specimens': total_specimens
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
@any_authenticated_user
def bulk_delete_specimens(request):
    """
    Bulk delete multiple specimens
    Expects a JSON body with specimen_ids array
    Example: {"specimen_ids": ["1000", "1001", "1002"]}
    """
    try:
        data = json.loads(request.body)
        specimen_ids = data.get('specimen_ids', [])
        
        if not specimen_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No specimen_ids provided'
            }, status=400)
        
        db = connection.get_db()
        specimens_collection = db.specimens
        
        # Get specimens to be deleted for media cleanup
        specimens_to_delete = specimens_collection.find({'specimen_id': {'$in': specimen_ids}})
        
        # Delete media folders for each specimen
        media_cleanup_results = []
        for specimen_doc in specimens_to_delete:
            specimen_oid = specimen_doc.get('_id')
            media_success, media_message = delete_specimen_media_folder(specimen_oid)
            media_cleanup_results.append({
                'specimen_id': specimen_doc.get('specimen_id', ''),
                'object_id': str(specimen_oid),
                'media_cleanup_success': media_success,
                'media_cleanup_message': media_message
            })
        
        # Delete all specimens with matching specimen_ids
        result = specimens_collection.delete_many(
            {'specimen_id': {'$in': specimen_ids}}
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Bulk delete completed. Deleted {result.deleted_count} specimens.',
            'results': {
                'requested_ids': specimen_ids,
                'total_requested': len(specimen_ids),
                'total_deleted': result.deleted_count,
                'not_found_count': len(specimen_ids) - result.deleted_count,
                'media_cleanup_results': media_cleanup_results
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
