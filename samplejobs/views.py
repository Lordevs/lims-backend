from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from .models import Job
from clients.models import Client  # Import Client model from clients app
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine import connection


# ============= UTILITY FUNCTIONS =============

def cascade_delete_job_relations(job_object_id, db):
    """
    Utility function to handle cascading deletes for a job
    This function soft-deletes all related entities when a job is deleted
    
    Args:
        job_object_id: The ObjectId of the job being deleted
        db: MongoDB database connection
    
    Returns:
        dict: Summary of cascaded deletions
    """
    deletion_summary = {}
    
    # 1. Soft delete all sample lots for this job
    sample_lots_collection = db.sample_lots
    sample_lots_result = sample_lots_collection.update_many(
        {'job_id': ObjectId(job_object_id), 'is_active': True},
        {'$set': {'is_active': False, 'updated_at': datetime.now()}}
    )
    deletion_summary['sample_lots'] = sample_lots_result.modified_count
    
    # 2. Future: Add more related entities here as the system grows
    # For example: sample preparations, tests, certificates, etc.
    # sample_preparations_collection = db.sample_preparations
    # sample_preparations_result = sample_preparations_collection.update_many(
    #     {'job_id': ObjectId(job_object_id), 'is_active': True},
    #     {'$set': {'is_active': False, 'updated_at': datetime.now()}}
    # )
    # deletion_summary['sample_preparations'] = sample_preparations_result.modified_count
    
    # Log the cascading operations for audit trail
    total_affected = sum(deletion_summary.values())
    print(f"Cascading delete summary for job {job_object_id}: {total_affected} total records affected")
    print(f"Details: {deletion_summary}")
    
    return deletion_summary


# ============= JOB CRUD ENDPOINTS =============

@csrf_exempt
@require_http_methods(["GET", "POST"])
def job_list(request):
    """
    List all jobs or create a new job
    GET: Returns list of all jobs with client information
    POST: Creates a new job
    """
    if request.method == 'GET':
        try:
            # Use raw query to avoid field validation issues with existing data
            from mongoengine import connection
            db = connection.get_db()
            jobs_collection = db.jobs
            
            jobs = jobs_collection.find({})
            data = []
            
            for job_doc in jobs:
                # Get client information
                client_name = "Unknown Client"
                try:
                    client = Client.objects.get(id=ObjectId(job_doc.get('client_id')))
                    client_name = client.client_name
                except (DoesNotExist, Exception):
                    pass
                
                # Only access fields that exist in our current model
                data.append({
                    'id': str(job_doc.get('_id', '')),
                    'job_id': job_doc.get('job_id', ''),
                    'client_id': str(job_doc.get('client_id', '')),
                    'client_name': client_name,
                    'project_name': job_doc.get('project_name', ''),
                    'end_user': job_doc.get('end_user', ''),
                    'receive_date': job_doc.get('receive_date').isoformat() if job_doc.get('receive_date') else '',
                    'received_by': job_doc.get('received_by', ''),
                    'remarks': job_doc.get('remarks', ''),
                    'job_created_at': job_doc.get('job_created_at').isoformat() if job_doc.get('job_created_at') else '',
                    'created_at': job_doc.get('created_at').isoformat() if job_doc.get('created_at') else '',
                    'updated_at': job_doc.get('updated_at').isoformat() if job_doc.get('updated_at') else ''
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

            # Auto-generate job_id if not provided
            if 'job_id' not in data or not data['job_id']:
                current_year = datetime.now().year
                year_prefix = f"MTL-{current_year}-"
                
                from mongoengine import connection
                db = connection.get_db()
                jobs_collection = db.jobs

                # Query for jobs from current year, sorted by job_id descending
                latest_job = jobs_collection.find(
                    {'job_id': {'$regex': f'^{year_prefix}', '$options': 'i'}}
                ).sort('job_id', -1).limit(1)
                latest_job_list = list(latest_job)

                if latest_job_list:
                    latest_job_id = latest_job_list[0]['job_id']
                    try:
                        sequence_part = latest_job_id.split('-')[-1]
                        next_sequence = int(sequence_part) + 1
                    except (ValueError, IndexError):
                        next_sequence = 1
                else:
                    next_sequence = 1

                formatted_sequence = str(next_sequence).zfill(4)
                generated_job_id = f"{year_prefix}{formatted_sequence}"

                # Check if generated job_id already exists (safety check)
                existing_check = jobs_collection.find_one({'job_id': generated_job_id})
                if existing_check:
                    while existing_check:
                        next_sequence += 1
                        formatted_sequence = str(next_sequence).zfill(4)
                        generated_job_id = f"{year_prefix}{formatted_sequence}"
                        existing_check = jobs_collection.find_one({'job_id': generated_job_id})

                data['job_id'] = generated_job_id

            # Validate required fields
            required_fields = ['job_id', 'client_id', 'project_name', 'receive_date', 'received_by']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)

            # Verify client exists
            try:
                client = Client.objects.get(id=ObjectId(data['client_id']))
            except (DoesNotExist, Exception) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Client not found: {str(e)}'
                }, status=400)

            # Parse receive_date
            try:
                receive_date = datetime.fromisoformat(data['receive_date'].replace('Z', '+00:00'))
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid receive_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }, status=400)

            job = Job(
                job_id=data['job_id'],
                client_id=ObjectId(data['client_id']),
                project_name=data['project_name'],
                end_user=data.get('end_user', ''),
                receive_date=receive_date,
                received_by=data['received_by'],
                remarks=data.get('remarks', '')
            )
            job.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Job created successfully',
                'data': {
                    'id': str(job.id),
                    'job_id': job.job_id,
                    'project_name': job.project_name,
                    'client_name': client.client_name
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
def job_detail(request, object_id):
    """
    Get, update, or delete a specific job by ObjectId
    GET: Returns job details with client information
    PUT: Updates job information
    DELETE: Deletes the job
    """
    try:
        # Convert string object_id to ObjectId
        try:
            object_id = ObjectId(object_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid ObjectId format: {str(e)}'
            }, status=400)
        
        # Use raw query to find job by ObjectId
        from mongoengine import connection
        db = connection.get_db()
        jobs_collection = db.jobs
        
        job_doc = jobs_collection.find_one({'_id': object_id})
        if not job_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Job not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get client information
            client_name = "Unknown Client"
            client_info = {}
            try:
                client = Client.objects.get(id=ObjectId(job_doc.get('client_id')))
                client_name = client.client_name
                client_info = {
                    'client_id': str(client.id),
                    'client_name': client.client_name,
                    'company_name': client.company_name,
                    'email': client.email,
                    'phone': client.phone
                }
            except DoesNotExist:
                pass
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(job_doc.get('_id', '')),
                    'job_id': job_doc.get('job_id', ''),
                    'client_id': str(job_doc.get('client_id', '')),
                    'client_info': client_info,
                    'project_name': job_doc.get('project_name', ''),
                    'end_user': job_doc.get('end_user', ''),
                    'receive_date': job_doc.get('receive_date').isoformat() if job_doc.get('receive_date') else '',
                    'received_by': job_doc.get('received_by', ''),
                    'remarks': job_doc.get('remarks', ''),
                    'job_created_at': job_doc.get('job_created_at').isoformat() if job_doc.get('job_created_at') else '',
                    'created_at': job_doc.get('created_at').isoformat() if job_doc.get('created_at') else '',
                    'updated_at': job_doc.get('updated_at').isoformat() if job_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update client_id if provided
                if 'client_id' in data:
                    try:
                        client = Client.objects.get(id=ObjectId(data['client_id']))
                        update_doc['client_id'] = ObjectId(data['client_id'])
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Client not found'
                        }, status=404)
                
                # Update other fields if provided
                if 'project_name' in data:
                    update_doc['project_name'] = data['project_name']
                if 'end_user' in data:
                    update_doc['end_user'] = data['end_user']
                if 'receive_date' in data:
                    try:
                        update_doc['receive_date'] = datetime.fromisoformat(data['receive_date'].replace('Z', '+00:00'))
                    except ValueError:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid receive_date format'
                        }, status=400)
                if 'received_by' in data:
                    update_doc['received_by'] = data['received_by']
                if 'remarks' in data:
                    update_doc['remarks'] = data['remarks']
                
                # Check if any fields were provided for update
                if not update_doc:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No fields provided for update'
                    }, status=400)
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Update the document
                result = jobs_collection.update_one(
                    {'_id': object_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated job document
                updated_job = jobs_collection.find_one({'_id': object_id})
                
                # Get updated client name
                client_name = "Unknown Client"
                try:
                    client = Client.objects.get(id=ObjectId(updated_job.get('client_id')))
                    client_name = client.client_name
                except DoesNotExist:
                    pass
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Job updated successfully',
                    'data': {
                        'id': str(updated_job.get('_id', '')),
                        'job_id': updated_job.get('job_id', ''),
                        'client_id': str(updated_job.get('client_id', '')),
                        'project_name': updated_job.get('project_name', ''),
                        'end_user': updated_job.get('end_user', ''),
                        'receive_date': updated_job.get('receive_date').isoformat() if updated_job.get('receive_date') else '',
                        'received_by': updated_job.get('received_by', ''),
                        'remarks': updated_job.get('remarks', ''),
                        'job_created_at': updated_job.get('job_created_at').isoformat() if updated_job.get('job_created_at') else '',
                        'created_at': updated_job.get('created_at').isoformat() if updated_job.get('created_at') else '',
                        'updated_at': updated_job.get('updated_at').isoformat() if updated_job.get('updated_at') else ''
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
            # Get the job's ObjectId for cascading delete
            job_object_id = job_doc.get('_id')
            job_info = {
                'id': str(job_doc.get('_id', '')),
                'job_id': job_doc.get('job_id', ''),
                'project_name': job_doc.get('project_name', ''),
                'client_id': str(job_doc.get('client_id', ''))
            }
            
            # Perform cascading delete using utility function
            deletion_summary = cascade_delete_job_relations(job_object_id, db)
            
            # Then delete the job itself
            result = jobs_collection.delete_one({'_id': object_id})
            if result.deleted_count == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Job not found'
                }, status=404)
            
            # Calculate total affected records
            total_cascaded = sum(deletion_summary.values())
            
            return JsonResponse({
                'status': 'success',
                'message': f'Job "{job_doc.get("job_id", "")}" deleted successfully. Also affected {total_cascaded} related records.',
                'cascaded_deletions': deletion_summary,
                'job_details': {
                    **job_info,
                    'deleted_at': datetime.now().isoformat()
                },
                'summary': {
                    'total_records_affected': total_cascaded + 1,  # +1 for the job itself
                    'job_deleted': True,
                    'cascading_successful': True
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def job_search(request):
    """
    Search jobs by various criteria
    Query parameters:
    - project: Search by project name (case-insensitive)
    - client_id: Search by client ID
    - received_by: Search by received_by field
    """
    try:
        # Get query parameters
        project = request.GET.get('project', '')
        client_id = request.GET.get('client_id', '')
        received_by = request.GET.get('received_by', '')
        
        # Build query for raw MongoDB
        query = {}
        if project:
            query['project_name'] = {'$regex': project, '$options': 'i'}
        if client_id:
            try:
                query['client_id'] = ObjectId(client_id)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid client_id format'
                }, status=400)
        if received_by:
            query['received_by'] = {'$regex': received_by, '$options': 'i'}
        
        # Use raw query to avoid field validation issues
        from mongoengine import connection
        db = connection.get_db()
        jobs_collection = db.jobs
        
        jobs = jobs_collection.find(query)
        
        data = []
        for job_doc in jobs:
            # Get client information
            client_name = "Unknown Client"
            try:
                client = Client.objects.get(id=ObjectId(job_doc.get('client_id')))
                client_name = client.client_name
            except (DoesNotExist, Exception):
                pass
            
            data.append({
                'id': str(job_doc.get('_id', '')),
                'job_id': job_doc.get('job_id', ''),
                'client_id': str(job_doc.get('client_id', '')),
                'client_name': client_name,
                'project_name': job_doc.get('project_name', ''),
                'receive_date': job_doc.get('receive_date').isoformat() if job_doc.get('receive_date') else '',
                'received_by': job_doc.get('received_by', '')
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'project': project,
                'client_id': client_id,
                'received_by': received_by
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def job_stats(request):
    """
    Get job statistics
    """
    try:
        # Use raw query to count jobs
        from mongoengine import connection
        db = connection.get_db()
        jobs_collection = db.jobs
        
        total_jobs = jobs_collection.count_documents({})
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_jobs': total_jobs
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def job_by_client(request, object_id):
    """
    Get all jobs for a specific client
    """
    try:
        # Convert string object_id to ObjectId
        try:
            object_id = ObjectId(object_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid ObjectId format: {str(e)}'
            }, status=400)
        
        # Verify client exists
        try:
            client = Client.objects.get(id=object_id)
        except (DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Client not found'
            }, status=404)
        
        # Use raw query to find jobs by client
        from mongoengine import connection
        db = connection.get_db()
        jobs_collection = db.jobs
        
        jobs = jobs_collection.find({'client_id': object_id})
        
        data = []
        for job_doc in jobs:
            data.append({
                'id': str(job_doc.get('_id', '')),
                'job_id': job_doc.get('job_id', ''),
                'project_name': job_doc.get('project_name', ''),
                'receive_date': job_doc.get('receive_date').isoformat() if job_doc.get('receive_date') else '',
                'received_by': job_doc.get('received_by', ''),
                'created_at': job_doc.get('created_at').isoformat() if job_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'client_info': {
                'client_id': str(client.id),
                'client_name': client.client_name,
                'company_name': client.company_name
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def bulk_delete_jobs(request):
    """
    Bulk delete multiple jobs with cascading delete
    Expects a JSON body with job_ids array
    Example: {"job_ids": ["MTL-2025-0001", "MTL-2025-0002"]}
    """
    try:
        data = json.loads(request.body)
        job_ids = data.get('job_ids', [])
        
        if not job_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No job_ids provided'
            }, status=400)
        
        db = connection.get_db()
        jobs_collection = db.jobs
        
        deleted_jobs = []
        total_cascaded = 0
        errors = []
        
        for job_id in job_ids:
            try:
                # Find the job
                job_doc = jobs_collection.find_one({'job_id': job_id})
                if not job_doc:
                    errors.append(f"Job {job_id} not found")
                    continue
                
                # Perform cascading delete
                job_object_id = job_doc.get('_id')
                deletion_summary = cascade_delete_job_relations(job_object_id, db)
                
                # Delete the job
                result = jobs_collection.delete_one({'job_id': job_id})
                if result.deleted_count > 0:
                    deleted_jobs.append({
                        'job_id': job_id,
                        'project_name': job_doc.get('project_name', ''),
                        'cascaded_deletions': deletion_summary
                    })
                    total_cascaded += sum(deletion_summary.values())
                else:
                    errors.append(f"Failed to delete job {job_id}")
                    
            except Exception as e:
                errors.append(f"Error deleting job {job_id}: {str(e)}")
        
        return JsonResponse({
            'status': 'success' if deleted_jobs else 'error',
            'message': f'Bulk delete completed. Deleted {len(deleted_jobs)} jobs with {total_cascaded} related records.',
            'results': {
                'deleted_jobs': deleted_jobs,
                'total_jobs_deleted': len(deleted_jobs),
                'total_cascaded_records': total_cascaded,
                'errors': errors
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
