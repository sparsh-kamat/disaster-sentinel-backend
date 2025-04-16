from django.shortcuts import render, get_object_or_404
from .models import ExistingAgencies
from .serializers import ExistingAgenciesSerializer
from rest_framework import filters

from rest_framework import generics

from rest_framework import viewsets, serializers, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import VolunteerInterest


# Import your serializers (adjust .serializers if necessary)
from .serializers import (
    VolunteerInterestSubmitSerializer,
    VolunteerInterestListSerializer,
    VolunteerInterestUpdateSerializer
)




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