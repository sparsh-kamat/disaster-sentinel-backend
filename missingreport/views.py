# missingreport/views.py

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser # <--- ADD JSONParser
from rest_framework.decorators import action, parser_classes as action_parser_classes # <--- ADD THIS
from django.utils import timezone # Ensure this is imported
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import action

from .models import MissingPersonReport
from users.models import CustomUser

from .serializers import (
    MissingPersonReportCreateSerializer,
    MissingPersonReportListSerializer,
    MissingPersonReportDetailSerializer,
    MissingPersonReportUpdateInfoSerializer, # New
    AgencyMarkFoundSerializer              # New
)

class MissingPersonReportViewSet(viewsets.ModelViewSet):
    queryset = MissingPersonReport.objects.all().select_related('reporter')
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return MissingPersonReportListSerializer
        elif self.action == 'create':
            return MissingPersonReportCreateSerializer
        elif self.action == 'update_additional_info': # For reporter editing info
            return MissingPersonReportUpdateInfoSerializer
        elif self.action == 'agency_mark_found': # For agency marking found
            return AgencyMarkFoundSerializer
        # Default for retrieve, update, partial_update (if not using custom actions for all updates)
        
        return MissingPersonReportDetailSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            # Extract validated data for model creation
            # Serializer already mapped frontend names to model field names via 'source'
            # or by matching names directly.
            validated_data = serializer.validated_data
            reporter_id = validated_data.pop('reporter_id')

            try:
                 reporter_user = CustomUser.objects.get(pk=reporter_id)
            except CustomUser.DoesNotExist:
                 return Response({'reporter_id': 'Invalid reporter user ID provided.'}, status=status.HTTP_400_BAD_REQUEST)

            # Get files directly from request.FILES using keys from your React form
            # Frontend form uses name="idCard" and name="photo"
            identity_card_file = request.FILES.get('idCard')
            person_photo_file = request.FILES.get('photo')

            # Validation for required person_photo
            if not person_photo_file and not MissingPersonReport._meta.get_field('person_photo').blank:
                 return Response({'photo': 'Person photo is required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Create the report instance
            # The validated_data from the serializer now contains keys matching the model fields
            # due to the 'source' attribute or direct name match in the serializer.
            report = MissingPersonReport.objects.create(
                reporter=reporter_user,
                identity_card_image=identity_card_file,
                person_photo=person_photo_file,
                # Pass other validated fields.
                # Serializer's validated_data keys should now align with model fields
                # e.g., validated_data['full_name'], validated_data['last_seen_location'], etc.
                **validated_data
            )

            output_serializer = MissingPersonReportDetailSerializer(report, context=self.get_serializer_context())
            headers = self.get_success_headers(output_serializer.data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error creating MissingPersonReport: {e}")
            # import traceback; traceback.print_exc()
            return Response({'error':'An internal server error occurred during report creation.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['patch'], url_path='update-info')
    def update_additional_info(self, request, pk=None):
        report = self.get_object()
        # !!! In a real app, add permission check: if request.user != report.reporter: return 403
        
        # Expected: reporter_id is sent in request body to verify ownership (since no auth)
        requesting_user_id = request.data.get('reporter_id')
        if not requesting_user_id or report.reporter_id != int(requesting_user_id):
             return Response({'detail': 'Reporter ID mismatch or not provided.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MissingPersonReportUpdateInfoSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(MissingPersonReportDetailSerializer(report).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Custom action for the original reporter to mark as found
    @action(detail=True, methods=['post'], url_path='reporter-mark-found')
    @action_parser_classes([JSONParser]) # <--- ADD THIS DECORATOR
    def reporter_mark_found(self, request, pk=None):
        report = self.get_object()
        # !!! In a real app, add permission check: if request.user != report.reporter: return 403
        
        # Expected: reporter_id is sent in request body to verify ownership
        requesting_user_id = request.data.get('reporter_id')
        if not requesting_user_id or report.reporter_id != int(requesting_user_id):
             return Response({'detail': 'Reporter ID mismatch or not provided.'}, status=status.HTTP_403_FORBIDDEN)

        if report.is_found:
            return Response({'message': 'Person already marked as found.'}, status=status.HTTP_400_BAD_REQUEST)

        report.is_found = True
        report.found_date = timezone.now().date()
        report.marked_found_by_type = 'REPORTER'
        try: # Ensure reporter_user can be fetched.
            report.marked_found_by_user = CustomUser.objects.get(pk=requesting_user_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Marking user not found.'}, status=status.HTTP_400_BAD_REQUEST)

        report.save()
        return Response(MissingPersonReportDetailSerializer(report).data)

    # Custom action for an agency to mark as found
    @action(detail=True, methods=['post'], url_path='agency-mark-found')
    def agency_mark_found(self, request, pk=None):
        report = self.get_object()
        # !!! In a real app, add permission check: if request.user.role != 'agency': return 403
        
        # Expected: agency_user_id is sent in request body
        agency_user_id = request.data.get('agency_user_id')
        if not agency_user_id:
            return Response({'detail': 'Agency user ID not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agency_user = CustomUser.objects.get(pk=agency_user_id, role='agency')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Agency user not found or not an agency role.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AgencyMarkFoundSerializer(data=request.data)
        if serializer.is_valid():
            report.is_found = True
            report.found_date = serializer.validated_data['found_date']
            report.marked_found_by_type = 'AGENCY'
            report.marked_found_by_user = agency_user
            report.agency_found_location = serializer.validated_data['agency_found_location']
            report.agency_current_location_of_person = serializer.validated_data.get('agency_current_location_of_person')
            report.agency_person_condition = serializer.validated_data['agency_person_condition']
            report.agency_found_notes = serializer.validated_data.get('agency_found_notes')
            report.save()
            return Response(MissingPersonReportDetailSerializer(report).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

