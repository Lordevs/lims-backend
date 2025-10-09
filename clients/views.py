from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from .models import Client
from mongoengine.errors import DoesNotExist, ValidationError
from authentication.decorators import any_authenticated_user
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def client_list(request):
    """
    List all clients or create a new client
    GET: Returns list of all clients
    POST: Creates a new client
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get clients with pagination
            clients_queryset = Client.objects.all().order_by('-created_at')
            paginated_clients, total_records = paginate_queryset(clients_queryset, page, limit)
            
            data = []
            for client in paginated_clients:
                data.append({
                    'id': str(client.id),
                    'client_name': client.client_name,
                    'company_name': client.company_name,
                    'email': client.email,
                    'phone': client.phone,
                    'address': client.address,
                    'contact_person': client.contact_person,
                    'is_active': client.is_active,
                    'created_at': client.created_at.isoformat(),
                    'updated_at': client.updated_at.isoformat()
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
            
            # Validate required fields (client_id is now optional and will be auto-generated)
            required_fields = ['client_name', 'email', 'phone', 'address', 'contact_person']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Handle client_id - can be provided as integer or will be auto-generated
            client_id = data.get('client_id')
            if client_id is not None:
                try:
                    client_id = int(client_id)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'client_id must be an integer if provided'
                    }, status=400)
            
            client = Client(
                client_id=client_id,  # Optional - will be auto-generated if None
                client_name=data['client_name'],
                company_name=data.get('company_name', ''),
                email=data['email'],
                phone=data['phone'],
                address=data['address'],
                contact_person=data['contact_person'],
                is_active=data.get('is_active', True)
            )
            client.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Client created successfully',
                'data': {
                    'id': str(client.id),
                    'client_id': client.client_id,
                    'client_name': client.client_name,
                    'email': client.email
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
def client_detail(request, object_id):
    """
    Get, update, or delete a specific client by ObjectId
    GET: Returns client details
    PUT: Updates client information
    DELETE: Deletes the client
    """
    try:
        # Convert object_id to ObjectId
        try:
            from bson import ObjectId
            object_id = ObjectId(object_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid ObjectId format: {str(e)}'
            }, status=400)
            
        client = Client.objects.get(id=object_id)
        
        if request.method == 'GET':
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(client.id),
                    'client_name': client.client_name,
                    'company_name': client.company_name,
                    'email': client.email,
                    'phone': client.phone,
                    'address': client.address,
                    'contact_person': client.contact_person,
                    'is_active': client.is_active,
                    'created_at': client.created_at.isoformat(),
                    'updated_at': client.updated_at.isoformat()
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document for partial update
                update_doc = {}
                
                # Only update fields that are provided in the request
                if 'client_name' in data:
                    update_doc['client_name'] = data['client_name']
                if 'company_name' in data:
                    update_doc['company_name'] = data['company_name']
                if 'email' in data:
                    update_doc['email'] = data['email']
                if 'phone' in data:
                    update_doc['phone'] = data['phone']
                if 'address' in data:
                    update_doc['address'] = data['address']
                if 'contact_person' in data:
                    update_doc['contact_person'] = data['contact_person']
                if 'is_active' in data:
                    update_doc['is_active'] = data['is_active']
                
                # Add updated timestamp
                update_doc['updated_at'] = datetime.now()
                
                # Use update() method for partial updates to avoid validation of unchanged fields
                if update_doc:
                    client.update(**update_doc)
                    # Refresh the client object to get updated data
                    client.reload()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Client updated successfully',
                    'data': {
                        'id': str(client.id),
                        'client_name': client.client_name,
                        'company_name': client.company_name,
                        'email': client.email,
                        'phone': client.phone,
                        'address': client.address,
                        'contact_person': client.contact_person,
                        'is_active': client.is_active,
                        'created_at': client.created_at.isoformat(),
                        'updated_at': client.updated_at.isoformat()
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
            client.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Client deleted successfully'
            })
            
    except DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Client not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def client_search(request):
    """
    Search clients by various criteria
    Query parameters:
    - name: Search by client name (case-insensitive)
    - email: Search by email
    - company: Search by company name
    - active: Filter by active status (true/false)
    """
    try:
        # Get query parameters
        name = request.GET.get('name', '')
        email = request.GET.get('email', '')
        company = request.GET.get('company', '')
        active = request.GET.get('active', '')
        
        # Build query
        query = {}
        if name:
            query['client_name__icontains'] = name
        if email:
            query['email__icontains'] = email
        if company:
            query['company_name__icontains'] = company
        if active:
            query['is_active'] = active.lower() == 'true'
        
        clients = Client.objects.filter(**query)
        
        data = []
        for client in clients:
            data.append({
                'id': str(client.id),
                'client_id': client.client_id,
                'client_name': client.client_name,
                'company_name': client.company_name,
                'email': client.email,
                'phone': client.phone,
                'is_active': client.is_active
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'name': name,
                'email': email,
                'company': company,
                'active': active
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def client_stats(request):
    """
    Get client statistics
    """
    try:
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()
        inactive_clients = Client.objects.filter(is_active=False).count()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'inactive_clients': inactive_clients,
                'activity_rate': round((active_clients / total_clients * 100), 2) if total_clients > 0 else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
