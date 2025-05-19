from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import (
    viewsets,
    status,
    permissions,
    serializers,
    generics,
    filters,
)
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction # For atomic updates

from .models import (
    AgencyProfile,
    AgencyImage,
    ExistingAgencies,
    Event,
    VolunteerInterest,
    EventInterest,
)
from .serializers import (
    AgencyProfileCreateSerializer,
    AgencyProfileDetailSerializer,
    AgencyProfileListSerializer,
    AgencyProfileUpdateSerializer,
    AgencyImageSerializer,
    ExistingAgenciesSerializer,
    EventSerializer,
    VolunteerInterestSubmitSerializer,
    VolunteerInterestListSerializer,
    VolunteerInterestUpdateSerializer,
    EventInterestSerializer,
)

from django_filters.rest_framework import DjangoFilterBackend # Import DjangoFilterBackend


User = get_user_model()

from .models import AgencyMemberPermission

# Adjust serializer imports
from .serializers import (
    AgencyMemberPermissionDetailSerializer,
    AgencyMemberPermissionUpdateSerializer
)

class AgencyPermissionListView(APIView):
    """
    Lists all permissions granted by a specific agency.
    Handles GET requests to /api/agency/<agency_id>/permissions/
    NO Authentication/Permissions applied.
    """
    permission_classes = [permissions.AllowAny] # Public access

    def get(self, request, agency_id, *args, **kwargs):
        # Optional: Check if agency_id corresponds to an actual agency user
        agency = get_object_or_404(User, pk=agency_id, role='agency')

        # Fetch permissions granted BY this agency, prefetch member details
        permissions = AgencyMemberPermission.objects.filter(
            agency=agency
        ).select_related('member') # Efficiently fetch related member data

        # Serialize the results using the detail serializer
        serializer = AgencyMemberPermissionDetailSerializer(permissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AgencyMemberPermissionManageView(APIView):
    """
    Manages permissions for a specific member under a specific agency.
    Handles GET, PUT, PATCH, DELETE requests to:
    /api/agency/<agency_id>/permissions/<member_id>/
    NO Authentication/Permissions applied.
    """
    permission_classes = [permissions.AllowAny] # Public access

    def get_object(self, agency_id, member_id):
        """Helper method to get the permission object or raise 404."""
        # Optional: Validate agency_id and member_id first
        get_object_or_404(User, pk=agency_id, role='agency')
        get_object_or_404(User, pk=member_id) # Ensure member exists

        # Find the specific permission record
        obj = get_object_or_404(AgencyMemberPermission, agency_id=agency_id, member_id=member_id)
        return obj

    def get(self, request, agency_id, member_id, *args, **kwargs):
        """Retrieve permissions for a specific member."""
        permission = self.get_object(agency_id, member_id)
        serializer = AgencyMemberPermissionDetailSerializer(permission)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic # Ensure database consistency during update/create
    def put(self, request, agency_id, member_id, *args, **kwargs):
        """Set/Replace permissions for a member (Creates if not exists)."""
        # Validate agency and member exist
        try:
            agency = User.objects.get(pk=agency_id, role='agency')
            member = User.objects.get(pk=member_id) # Consider adding role='user' check
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid agency or member ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get existing or initialize new permission object
        # Using get_or_create is slightly cleaner than try/except get_object_or_404
        permission_obj, created = AgencyMemberPermission.objects.get_or_create(
            agency=agency,
            member=member
            # Defaults are handled by the model definition
        )

        # Use the Update serializer to validate incoming permission flags
        # Pass the instance to update, ensure all fields are provided for PUT
        serializer = AgencyMemberPermissionUpdateSerializer(permission_obj, data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            updated_permission = serializer.save()
            # Return the updated data using the Detail serializer
            response_serializer = AgencyMemberPermissionDetailSerializer(updated_permission)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(response_serializer.data, status=status_code)
        except serializers.ValidationError as e:
             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error setting permissions for member {member_id} under agency {agency_id}: {e}")
            return Response({'error': 'An internal server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def patch(self, request, agency_id, member_id, *args, **kwargs):
        """Partially update permissions for a member."""
        permission_obj = self.get_object(agency_id, member_id) # Raises 404 if not found

        # Use the Update serializer with partial=True
        serializer = AgencyMemberPermissionUpdateSerializer(permission_obj, data=request.data, partial=True)

        try:
            serializer.is_valid(raise_exception=True)
            updated_permission = serializer.save()
            # Return the updated data using the Detail serializer
            response_serializer = AgencyMemberPermissionDetailSerializer(updated_permission)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error patching permissions for member {member_id} under agency {agency_id}: {e}")
            return Response({'error': 'An internal server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def delete(self, request, agency_id, member_id, *args, **kwargs):
        """Remove all permissions for a member under an agency."""
        permission = self.get_object(agency_id, member_id) # Raises 404 if not found
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class AgencyProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Agency Profiles.
    Handles List, Create (with images), Retrieve, Update, Delete (profile).
    NO Authentication or Permissions applied.
    """
    queryset = AgencyProfile.objects.all().select_related('user').prefetch_related('images')
    parser_classes = [MultiPartParser, FormParser] # Handles file uploads
    permission_classes = [permissions.AllowAny] # Public access

    def get_serializer_class(self):
        """Choose serializer based on action."""
        if self.action == 'list':
            return AgencyProfileListSerializer
        elif self.action == 'create':
            return AgencyProfileCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AgencyProfileUpdateSerializer
        # Default for 'retrieve'
        return AgencyProfileDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Override create to handle user_id input and image uploads.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Extract user_id before creating profile instance
            user_id = serializer.validated_data.pop('user_id')
            try:
                 # Fetch the user specified by user_id
                 agency_user = User.objects.get(pk=user_id, role='agency')
            except User.DoesNotExist:
                 # This should ideally be caught by serializer's validate_user_id,
                 # but handle here just in case.
                 return Response({'user_id': 'Invalid user ID provided or user is not an agency.'}, status=status.HTTP_400_BAD_REQUEST)

            # Create the profile instance, linking the fetched user
            # Pass the remaining validated data
            profile = AgencyProfile.objects.create(user=agency_user, **serializer.validated_data)

            # Handle Image Uploads separately after profile is created
            images_data = request.FILES.getlist('images')
            for image_data in images_data:
                # Create AgencyImage linked to the profile, Cloudinary handles upload
                AgencyImage.objects.create(agency_profile=profile, image=image_data)

            # Return response using the Detail serializer to show created object with images
            output_serializer = AgencyProfileDetailSerializer(profile, context=self.get_serializer_context())
            headers = self.get_success_headers(output_serializer.data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except serializers.ValidationError as e:
            # Catch validation errors from serializer (inc. validate_user_id)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catch other potential errors during creation
            print(f"Error creating AgencyProfile: {e}") # Basic logging
            return Response({'error':'An internal server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic # Ensure atomicity for profile text and new image updates
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update to handle updates to text fields
        AND allow adding new images.
        """
        instance = self.get_object() # Get the AgencyProfile instance

        # --- Handle Text Field Updates ---
        # We only want to pass non-file data to AgencyProfileUpdateSerializer
        profile_text_data = {}
        has_text_data_to_update = False
        for key in request.data:
            if key not in request.FILES: # Check if the key is not for a file
                profile_text_data[key] = request.data[key]
                has_text_data_to_update = True
        
        if has_text_data_to_update:
            # Use AgencyProfileUpdateSerializer for the text fields
            profile_serializer = AgencyProfileUpdateSerializer(instance, data=profile_text_data, partial=True)
            try:
                profile_serializer.is_valid(raise_exception=True)
                profile_serializer.save() # Save changes to text fields
            except serializers.ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e: # Catch other potential errors during profile save
                print(f"Error updating AgencyProfile text fields: {e}")
                return Response(
                    {'error':'An error occurred while updating profile details.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # --- Handle Adding New Images ---
        # The key 'images' should match what the frontend sends in FormData
        new_images_data = request.FILES.getlist('images')
        if new_images_data:
            for image_data in new_images_data:
                try:
                    AgencyImage.objects.create(agency_profile=instance, image=image_data)
                except Exception as e: # Catch errors during image creation/upload
                    print(f"Error creating AgencyImage: {e}")
                    # Decide on error handling: continue, or return error for the whole request?
                    # For now, let's return an error if any image fails.
                    return Response(
                        {'error': f'An error occurred while uploading new image: {image_data.name}.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        # Refresh the instance from DB to get all updates including newly added images
        instance.refresh_from_db()
        
        # Return the full updated profile using the Detail serializer
        detail_serializer = AgencyProfileDetailSerializer(instance, context=self.get_serializer_context())
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    # Default methods for retrieve, update, partial_update, destroy will now use
    # the serializers selected by get_serializer_class.
    # Update/Partial Update uses AgencyProfileUpdateSerializer.
    # Retrieve uses AgencyProfileDetailSerializer.
    # List uses AgencyProfileListSerializer.
    # Destroy works on the AgencyProfile.

class CheckVolunteerRequestStatusView(APIView):
    """
    Checks if a user can submit a new volunteer request to a specific agency,
    or if an existing request or agency membership (with permissions) already exists.
    """
    permission_classes = [permissions.AllowAny] # As per your project's current setup

    def get(self, request, *args, **kwargs):
        volunteer_id = request.query_params.get('volunteer_id')
        agency_id = request.query_params.get('agency_id')

        if not volunteer_id or not agency_id:
            return Response(
                {"error": "Both volunteer_id and agency_id query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            volunteer_id = int(volunteer_id)
            agency_id = int(agency_id)
        except ValueError:
            return Response(
                {"error": "volunteer_id and agency_id must be integers."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            volunteer = get_object_or_404(User, pk=volunteer_id)
            agency = get_object_or_404(User, pk=agency_id, role='agency')
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid volunteer_id or agency_id, or agency_id does not belong to an agency."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check 1: Existing VolunteerInterest request
        # You might want to filter for non-rejected requests if applicable
        existing_volunteer_request = VolunteerInterest.objects.filter(
            volunteer=volunteer,
            agency=agency
            # Consider adding: .exclude(status='REJECTED') if you have a status field
        ).first()

        if existing_volunteer_request:
            return Response({
                "can_submit_new_request": False,
                "reason_code": "EXISTING_VOLUNTEER_REQUEST",
                "message": "An active or pending volunteer request already exists for this agency.",
                "existing_request_details": {
                    "id": existing_volunteer_request.id,
                    "submitted_at": existing_volunteer_request.submitted_at,
                    "is_accepted": existing_volunteer_request.is_accepted
                }
            }, status=status.HTTP_200_OK)

        # Check 2: Existing AgencyMemberPermission
        existing_permission = AgencyMemberPermission.objects.filter(
            member=volunteer,
            agency=agency
        ).first()

        if existing_permission:
            return Response({
                "can_submit_new_request": False,
                "reason_code": "ALREADY_AGENCY_MEMBER",
                "message": "This user is already associated with the agency and has defined permissions.",
                "member_permission_details": {
                    "granted_at": existing_permission.granted_at,
                    # Add any relevant permission flags if needed, e.g.:
                    # "is_agency_admin": existing_permission.is_agency_admin
                }
            }, status=status.HTTP_200_OK)

        # If neither condition is met, the user can submit a new request
        return Response({
            "can_submit_new_request": True,
            "reason_code": "ALLOW_NEW",
            "message": "User can submit a new volunteer request."
        }, status=status.HTTP_200_OK)


class AgencyImageDeleteView(APIView):
    """
    Allows deleting a specific AgencyImage by its ID.
    NO Authentication or Permissions applied.
    """
    permission_classes = [permissions.AllowAny] # Public access

    def delete(self, request, pk, format=None):
        image_instance = get_object_or_404(AgencyImage, pk=pk)

        # --- Permission Check REMOVED as requested ---
        # Original Check (for reference):
        # if image_instance.agency_profile.user != request.user:
        #     return Response(...)
        # --- End Removed Check ---

        # Delete the image record (Cloudinary file might need separate cleanup later if desired)
        image_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class VolunteerInterestViewSet(viewsets.ModelViewSet):
    queryset = VolunteerInterest.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return VolunteerInterestSubmitSerializer
        elif self.action == 'partial_update' or self.action == 'update':
            return VolunteerInterestUpdateSerializer
        return VolunteerInterestListSerializer

    def get_queryset(self):
        agency_id = self.request.query_params.get('agency_id', None)
        if agency_id:
            return VolunteerInterest.objects.filter(agency__id=agency_id)
        return VolunteerInterest.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = VolunteerInterestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interest = serializer.save()
        return Response(VolunteerInterestListSerializer(interest).data, status=status.HTTP_201_CREATED)
    # delete
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # update
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = VolunteerInterestUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['post'], url_path='accept')
    def accept_volunteer(self, request, pk=None):
        interest = self.get_object()

        # Optional: you can add auth and role check here
        if request.user.is_authenticated and request.user != interest.agency:
            return Response({'detail': 'Only the agency can accept this interest.'}, status=403)

        serializer = VolunteerInterestUpdateSerializer(interest, data={"is_accepted": True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Volunteer accepted successfully!'})
    
    
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        # Get the user_id from the request data
        user_id = self.request.data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)  # Fetch user by user_id
                # Save the event with the correct user_id (not the user object)
                serializer.save(user_id=user.id)  # Save only the user ID, not the user object
            except User.DoesNotExist:
                raise ValueError(f"User with id {user_id} does not exist.")
        else:
            raise ValueError("User ID is required to create an event.")

    @action(detail=True, methods=['post'])
    def add_timeline(self, request, pk=None):
        """
        Custom action to add timeline items to an event.
        """
        event = self.get_object()
        timeline_items_data = request.data.get('timeline_items', [])
        
        if timeline_items_data:
            event.timeline_items.extend(timeline_items_data)  # Append new timeline items
            event.save()  # Save the event after updating the timeline items
            
        return Response({'status': 'Timeline items added', 'timeline_items': event.timeline_items})

    def get_queryset(self):
        """
        If 'user_id' is in the request, filter events by that user.
        Otherwise, return all events.
        """
        queryset = Event.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
class ExistingAgenciesListView(generics.ListAPIView):
    queryset = ExistingAgencies.objects.all()
    serializer_class = ExistingAgenciesSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = '__all__'  # Allow ordering by any field in the model

    def get_queryset(self):
        queryset = ExistingAgencies.objects.all()

        # Check if the 'state' parameter is in the request
        state = self.request.query_params.get('state', None)
        if state:
            # Filter disasters by state
            queryset = queryset.filter(state=state)
        
        return queryset
# This will render the 'welcome.html' template


# --- NEW VIEWSET FOR EVENT INTEREST ---
class EventInterestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to express or withdraw interest in an event.
    """
    queryset = EventInterest.objects.all()
    serializer_class = EventInterestSerializer
    filter_backends = [DjangoFilterBackend] # Add DjangoFilterBackend
    filterset_fields = ['user', 'event']    # Allow filtering on user and event ForeignKeys by their IDs

    def get_queryset(self):
        """
        Optionally, ensure users can only see their own interest records
        when listing without specific user/event filters for privacy,
        unless they are admins or have specific permissions.
        For a specific check (user+event), this is less critical as it's targeted.
        """
        # If you want to restrict general listing to the current user:
        # return EventInterest.objects.filter(user=self.request.user)
        # For now, allowing general filtering by ID as specified in filterset_fields.
        return super().get_queryset()

    def perform_create(self, serializer):
        # SECURITY NOTE:
        # It's highly recommended to use request.user instead of user_id from payload
        # for actions tied to the logged-in user.
        # Example: user = self.request.user
        # However, to follow your current pattern of sending user_id:
        user_id_from_payload = self.request.data.get('user_id')
        event_id_from_payload = self.request.data.get('event_id')
        interested_status = self.request.data.get('interested', False) # Default to False if not provided

        if not user_id_from_payload or not event_id_from_payload:
            raise serializers.ValidationError("Both 'user_id' and 'event_id' are required.")

        try:
            user = User.objects.get(id=user_id_from_payload)
            # Security check: Ensure the user_id from payload matches the authenticated user
            if user != self.request.user:
                 raise serializers.ValidationError("You can only set interest for yourself.") # Or return 403 Forbidden
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with id {user_id_from_payload} does not exist.")

        try:
            event = Event.objects.get(id=event_id_from_payload)
        except Event.DoesNotExist:
            raise serializers.ValidationError(f"Event with id {event_id_from_payload} does not exist.")

        # The serializer's create method now handles the update_or_create logic
        serializer.save(user_id=user_id_from_payload, event_id=event_id_from_payload, interested=interested_status)

    def create(self, request, *args, **kwargs):
        """
        Handles POST request to create or update an EventInterest.
        Expects: {"user_id": <id>, "event_id": <id>, "interested": true/false}
        """
        # SECURITY NOTE: Ideally, use request.user.id for user_id.
        # Forcing user_id to be the authenticated user if it's part of the payload:
        # mutable_data = request.data.copy()
        # mutable_data['user_id'] = request.user.id
        # serializer = self.get_serializer(data=mutable_data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer) # This will call serializer.save() which calls serializer.create()
        headers = self.get_success_headers(serializer.data)
        # The serializer.data after save should reflect the created/updated object.
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # You might not need standard list, retrieve, update, destroy for this model,
    # if POST to create is used as an "upsert" (update or create).
    # If you do, they will work by default.
    # Consider overriding update if you want PUT to behave specifically.