from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from bson import ObjectId
from .models import WelderCard
from welders.models import Welder
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine import connection
from authentication.decorators import any_authenticated_user, welding_operations_required
from lims_backend.utilities.pagination import get_pagination_params, create_pagination_response, paginate_queryset


@csrf_exempt
@require_http_methods(["GET", "POST"])
@any_authenticated_user
def welder_card_list(request):
    """
    List all welder cards or create a new welder card
    GET: Returns list of all welder cards with welder information
    POST: Creates a new welder card
    """
    if request.method == 'GET':
        try:
            # Get pagination parameters
            page, limit, offset = get_pagination_params(request)
            
            # Get search parameters
            card_no_search = request.GET.get('card_no', '')
            company_search = request.GET.get('company', '')
            welder_name_search = request.GET.get('welder_name', '')
            
            # Get filtering parameters
            show_inactive = request.GET.get('show_inactive', '').lower() == 'true'
            include_inactive = request.GET.get('include_inactive', '').lower() == 'true'
            
            # Use raw query to avoid field validation issues with existing data
            db = connection.get_db()
            welder_cards_collection = db.welder_cards
            
            # Build query based on search parameters
            query = {}
            if card_no_search:
                query['card_no'] = {'$regex': card_no_search, '$options': 'i'}
            if company_search:
                query['company'] = {'$regex': company_search, '$options': 'i'}
            
            # Handle welder name search - need to find welder IDs first using raw MongoDB query
            if welder_name_search:
                try:
                    welders_collection = db.welders
                    welder_docs = welders_collection.find({
                        'operator_name': {'$regex': welder_name_search, '$options': 'i'}
                    })
                    welder_ids = [doc['_id'] for doc in welder_docs]
                    
                    if welder_ids:
                        query['welder_id'] = {'$in': welder_ids}
                    else:
                        # No welders found with that name, return empty result
                        query['welder_id'] = {'$in': []}
                except Exception:
                    # If there's an error, return empty result
                    query['welder_id'] = {'$in': []}
            
            # Add filtering based on is_active status
            if show_inactive:
                # Only show inactive welder cards
                query['is_active'] = False
            elif include_inactive:
                # Show both active and inactive welder cards (no filter)
                pass
            else:
                # Default: only show active welder cards
                query['is_active'] = True
            
            # Get total count for pagination
            total_records = welder_cards_collection.count_documents(query)
            
            # Get paginated welder cards
            welder_cards = welder_cards_collection.find(query).skip(offset).limit(limit).sort('created_at', -1)
            data = []
            
            for card_doc in welder_cards:
                # Get welder information using raw MongoDB query
                welder_name = "Unknown Welder"
                welder_info = {}
                try:
                    welders_collection = db.welders
                    welder_obj_id = card_doc.get('welder_id')
                    if welder_obj_id:
                        # Handle both ObjectId and string welder_id
                        if isinstance(welder_obj_id, str):
                            welder_obj_id = ObjectId(welder_obj_id)
                        welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                        if welder_doc:
                            welder_info = {
                                'welder_id': str(welder_doc.get('_id', '')),
                                'operator_name': welder_doc.get('operator_name', ''),
                                'operator_id': welder_doc.get('operator_id', ''),
                                'iqama': welder_doc.get('iqama', ''),
                                'profile_image': f"{settings.MEDIA_URL}{welder_doc.get('profile_image', '')}" if welder_doc.get('profile_image', '') else None
                            }
                except Exception:
                    pass
                
                data.append({
                    'id': str(card_doc.get('_id', '')),
                    'company': card_doc.get('company', ''),
                    'welder_id': str(card_doc.get('welder_id', '')),
                    'welder_info': welder_info,
                    'authorized_by': card_doc.get('authorized_by', ''),
                    'welding_inspector': card_doc.get('welding_inspector', ''),
                    'law_name': card_doc.get('law_name', ''),
                    'card_no': card_doc.get('card_no', ''),
                    'attributes': card_doc.get('attributes', {}),
                    'is_active': card_doc.get('is_active', True),
                    'created_at': card_doc.get('created_at').isoformat() if card_doc.get('created_at') else '',
                    'updated_at': card_doc.get('updated_at').isoformat() if card_doc.get('updated_at') else ''
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
            required_fields = ['company', 'welder_id', 'authorized_by', 'welding_inspector', 'law_name', 'card_no']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty'
                    }, status=400)
            
            # Verify welder exists
            try:
                welder = Welder.objects.get(id=ObjectId(data['welder_id']))
            except (DoesNotExist, Exception) as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Welder not found: {str(e)}'
                }, status=400)
            
            welder_card = WelderCard(
                company=data['company'],
                welder_id=ObjectId(data['welder_id']),
                authorized_by=data['authorized_by'],
                welding_inspector=data['welding_inspector'],
                law_name=data['law_name'],
                card_no=data['card_no'],
                attributes=data.get('attributes', {}),
                is_active=data.get('is_active', True)
            )
            welder_card.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder card created successfully',
                'data': {
                    'id': str(welder_card.id),
                    'card_no': welder_card.card_no,
                    'company': welder_card.company,
                    'welder_name': welder.operator_name
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
def welder_card_detail(request, object_id):
    """
    Get, update, or delete a specific welder card by ObjectId
    GET: Returns welder card details with welder information
    PUT: Updates welder card information
    DELETE: Deletes the welder card
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
        
        # Use raw query to find welder card by ObjectId
        db = connection.get_db()
        welder_cards_collection = db.welder_cards
        
        card_doc = welder_cards_collection.find_one({'_id': object_id})
        if not card_doc:
            return JsonResponse({
                'status': 'error',
                'message': 'Welder card not found'
            }, status=404)
        
        if request.method == 'GET':
            # Get welder information using raw MongoDB query
            welder_name = "Unknown Welder"
            welder_info = {}
            try:
                welders_collection = db.welders
                welder_obj_id = card_doc.get('welder_id')
                if welder_obj_id:
                    # Handle both ObjectId and string welder_id
                    if isinstance(welder_obj_id, str):
                        welder_obj_id = ObjectId(welder_obj_id)
                    welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                    if welder_doc:
                        welder_info = {
                            'welder_id': str(welder_doc.get('_id', '')),
                            'operator_name': welder_doc.get('operator_name', ''),
                            'operator_id': welder_doc.get('operator_id', ''),
                            'iqama': welder_doc.get('iqama', ''),
                            # f"{settings.MEDIA_URL}{welder.profile_image}" if welder.profile_image else None
                            'profile_image': f"{settings.MEDIA_URL}{welder_doc.get('profile_image', '')}" if welder_doc.get('profile_image', '') else None
                            
                        }
            except Exception:
                pass
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'id': str(card_doc.get('_id', '')),
                    'company': card_doc.get('company', ''),
                    'welder_id': str(card_doc.get('welder_id', '')),
                    'welder_info': welder_info,
                    'authorized_by': card_doc.get('authorized_by', ''),
                    'welding_inspector': card_doc.get('welding_inspector', ''),
                    'law_name': card_doc.get('law_name', ''),
                    'card_no': card_doc.get('card_no', ''),
                    'attributes': card_doc.get('attributes', {}),
                    'is_active': card_doc.get('is_active', True),
                    'created_at': card_doc.get('created_at').isoformat() if card_doc.get('created_at') else '',
                    'updated_at': card_doc.get('updated_at').isoformat() if card_doc.get('updated_at') else ''
                }
            })
        
        elif request.method == 'PUT':
            try:
                data = json.loads(request.body)
                
                # Prepare update document
                update_doc = {}
                
                # Update welder_id if provided
                if 'welder_id' in data:
                    try:
                        welder = Welder.objects.get(id=ObjectId(data['welder_id']))
                        update_doc['welder_id'] = ObjectId(data['welder_id'])
                    except (DoesNotExist, Exception):
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Welder not found'
                        }, status=404)
                
                # Update other fields if provided
                if 'company' in data:
                    update_doc['company'] = data['company']
                if 'authorized_by' in data:
                    update_doc['authorized_by'] = data['authorized_by']
                if 'welding_inspector' in data:
                    update_doc['welding_inspector'] = data['welding_inspector']
                if 'law_name' in data:
                    update_doc['law_name'] = data['law_name']
                if 'card_no' in data:
                    update_doc['card_no'] = data['card_no']
                if 'attributes' in data:
                    update_doc['attributes'] = data['attributes']
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
                result = welder_cards_collection.update_one(
                    {'_id': object_id},
                    {'$set': update_doc}
                )
                
                if result.modified_count == 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No changes made'
                    }, status=400)
                
                # Get updated welder card document
                updated_card = welder_cards_collection.find_one({'_id': object_id})
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Welder card updated successfully',
                    'data': {
                        'id': str(updated_card.get('_id', '')),
                        'card_no': updated_card.get('card_no', ''),
                        'company': updated_card.get('company', ''),
                        'updated_at': updated_card.get('updated_at').isoformat() if updated_card.get('updated_at') else ''
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
            result = welder_cards_collection.update_one(
                {'_id': object_id},
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
                    'message': 'Welder card not found'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Welder card deactivated successfully',
                'data': {
                    'id': str(object_id),
                    'card_no': card_doc.get('card_no', ''),
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
def welder_card_search(request):
    """
    Search welder cards by various criteria
    Query parameters:
    - card_no: Search by card number (case-insensitive)
    - company: Search by company name (case-insensitive)
    - welder_id: Search by welder ID
    - authorized_by: Search by authorized by field
    - q: Global search across all text fields (card_no, company, authorized_by, welding_inspector, law_name, welder_name)
    """
    try:
        # Get query parameters
        card_no = request.GET.get('card_no', '')
        company = request.GET.get('company', '')
        welder_id = request.GET.get('welder_id', '')
        authorized_by = request.GET.get('authorized_by', '')
        q = request.GET.get('q', '')  # Global search parameter
        
        # Build query for raw MongoDB
        query = {}
        if card_no:
            query['card_no'] = {'$regex': card_no, '$options': 'i'}
        if company:
            query['company'] = {'$regex': company, '$options': 'i'}
        if welder_id:
            try:
                query['welder_id'] = ObjectId(welder_id)
            except Exception:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid welder_id format'
                }, status=400)
        if authorized_by:
            query['authorized_by'] = {'$regex': authorized_by, '$options': 'i'}
        
        # Handle global search parameter 'q'
        if q:
            # Create OR conditions for global search across multiple fields
            or_conditions = [
                {'card_no': {'$regex': q, '$options': 'i'}},
                {'company': {'$regex': q, '$options': 'i'}},
                {'authorized_by': {'$regex': q, '$options': 'i'}},
                {'welding_inspector': {'$regex': q, '$options': 'i'}},
                {'law_name': {'$regex': q, '$options': 'i'}}
            ]
            
            # Add welder name to global search
            try:
                welders_collection = db.welders
                welder_docs = welders_collection.find({
                    'operator_name': {'$regex': q, '$options': 'i'}
                })
                welder_ids = [doc['_id'] for doc in welder_docs]
                if welder_ids:
                    or_conditions.append({'welder_id': {'$in': welder_ids}})
            except Exception:
                pass
            
            if query:
                # If we have other specific filters, combine them with AND
                query['$and'] = [
                    {k: v for k, v in query.items() if k != '$and'},
                    {'$or': or_conditions}
                ]
            else:
                query['$or'] = or_conditions
        
        # Use raw query to avoid field validation issues
        db = connection.get_db()
        welder_cards_collection = db.welder_cards
        
        welder_cards = welder_cards_collection.find(query)
        
        data = []
        for card_doc in welder_cards:
            # Get welder information using raw MongoDB query
            welder_name = "Unknown Welder"
            try:
                welders_collection = db.welders
                welder_obj_id = card_doc.get('welder_id')
                if welder_obj_id:
                    # Handle both ObjectId and string welder_id
                    if isinstance(welder_obj_id, str):
                        welder_obj_id = ObjectId(welder_obj_id)
                    welder_doc = welders_collection.find_one({'_id': welder_obj_id})
                    if welder_doc:
                        welder_name = welder_doc.get('operator_name', 'Unknown Welder')
            except Exception:
                pass
            
            data.append({
                'id': str(card_doc.get('_id', '')),
                'card_no': card_doc.get('card_no', ''),
                'company': card_doc.get('company', ''),
                'welder_id': str(card_doc.get('welder_id', '')),
                'welder_name': welder_name,
                'authorized_by': card_doc.get('authorized_by', ''),
                'is_active': card_doc.get('is_active', True)
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'filters_applied': {
                'card_no': card_no,
                'company': company,
                'welder_id': welder_id,
                'authorized_by': authorized_by,
                'q': q
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
def welder_card_stats(request):
    """
    Get comprehensive welder card statistics
    """
    try:
        from datetime import datetime, timedelta
        
        # Use raw query to count welder cards
        db = connection.get_db()
        welder_cards_collection = db.welder_cards
        
        # Basic counts
        total_cards = welder_cards_collection.count_documents({})
        active_cards = welder_cards_collection.count_documents({'is_active': True})
        inactive_cards = welder_cards_collection.count_documents({'is_active': False})
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_cards = welder_cards_collection.count_documents({'created_at': {'$gte': thirty_days_ago}})
        
        # Company distribution (top 10)
        company_stats = welder_cards_collection.aggregate([
            {'$match': {'company': {'$ne': ''}}},
            {'$group': {'_id': '$company', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])
        
        # Cards with attributes
        cards_with_attributes = welder_cards_collection.count_documents({'attributes': {'$exists': True, '$ne': {}}})
        
        # Recent cards (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_cards_week = welder_cards_collection.count_documents({'created_at': {'$gte': seven_days_ago}})
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'overview': {
                    'total_cards': total_cards,
                    'active_cards': active_cards,
                    'inactive_cards': inactive_cards,
                    'activity_rate': round((active_cards / total_cards * 100), 2) if total_cards > 0 else 0
                },
                'recent_activity': {
                    'new_cards_last_30_days': recent_cards,
                    'new_cards_last_7_days': recent_cards_week
                },
                'completion_rates': {
                    'cards_with_attributes': cards_with_attributes,
                    'cards_without_attributes': total_cards - cards_with_attributes,
                    'attribute_completion_rate': round((cards_with_attributes / total_cards * 100), 2) if total_cards > 0 else 0
                },
                'company_distribution': list(company_stats),
                'generated_at': datetime.now().isoformat()
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
def welder_card_by_welder(request, welder_id):
    """
    Get all welder cards for a specific welder
    """
    try:
        # Convert string welder_id to ObjectId
        try:
            welder_obj_id = ObjectId(welder_id)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid welder ID format: {str(e)}'
            }, status=400)
        
        # Verify welder exists
        try:
            welder = Welder.objects.get(id=welder_obj_id)
        except (DoesNotExist, Exception):
            return JsonResponse({
                'status': 'error',
                'message': 'Welder not found'
            }, status=404)
        
        # Use raw query to find welder cards by welder
        db = connection.get_db()
        welder_cards_collection = db.welder_cards
        
        welder_cards = welder_cards_collection.find({'welder_id': welder_obj_id})
        
        data = []
        for card_doc in welder_cards:
            data.append({
                'id': str(card_doc.get('_id', '')),
                'card_no': card_doc.get('card_no', ''),
                'company': card_doc.get('company', ''),
                'authorized_by': card_doc.get('authorized_by', ''),
                'welding_inspector': card_doc.get('welding_inspector', ''),
                'law_name': card_doc.get('law_name', ''),
                'is_active': card_doc.get('is_active', True),
                'created_at': card_doc.get('created_at').isoformat() if card_doc.get('created_at') else ''
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data),
            'welder_info': {
                'welder_id': str(welder.id),
                'operator_name': welder.operator_name,
                'operator_id': welder.operator_id,
                'iqama': welder.iqama
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)