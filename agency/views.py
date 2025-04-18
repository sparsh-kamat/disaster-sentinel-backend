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

from .models import (
    AgencyProfile,
    AgencyImage,
    ExistingAgencies,
    Event,
    VolunteerInterest,
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
)

User = get_user_model()

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
                 agency_user = CustomUser.objects.get(pk=user_id, role='agency')
            except CustomUser.DoesNotExist:
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

    # Default methods for retrieve, update, partial_update, destroy will now use
    # the serializers selected by get_serializer_class.
    # Update/Partial Update uses AgencyProfileUpdateSerializer.
    # Retrieve uses AgencyProfileDetailSerializer.
    # List uses AgencyProfileListSerializer.
    # Destroy works on the AgencyProfile.


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