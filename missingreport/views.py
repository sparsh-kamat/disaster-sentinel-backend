# missingreport/views.py

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction

# Adjust model imports
from .models import MissingPersonReport
from users.models import CustomUser # Assuming user model is in 'users' app

# Adjust serializer imports
from .serializers import (
    MissingPersonReportCreateSerializer,
    MissingPersonReportListSerializer,
    MissingPersonReportDetailSerializer
)

class MissingPersonReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Missing Person Reports.
    Handles List, Create (with direct images), Retrieve, Delete.
    Update (PUT/PATCH) is currently basic - needs custom logic for image updates.
    NO Authentication or Permissions applied.
    """
    queryset = MissingPersonReport.objects.all().select_related('reporter')
    parser_classes = [MultiPartParser, FormParser] # Handle file uploads
    permission_classes = [permissions.AllowAny] # Public access

    def get_serializer_class(self):
        """Choose serializer based on action."""
        if self.action == 'list':
            return MissingPersonReportListSerializer
        elif self.action == 'create':
            return MissingPersonReportCreateSerializer
        # Default for retrieve, update, partial_update
        return MissingPersonReportDetailSerializer

    @transaction.atomic # Ensure database consistency during creation
    def create(self, request, *args, **kwargs):
        """
        Override create to handle reporter_id input and direct file uploads
        for identity_card_image and person_photo.
        """
        # Use the appropriate serializer determined by get_serializer_class
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            reporter_id = serializer.validated_data.pop('reporter_id')
            try:
                 reporter_user = CustomUser.objects.get(pk=reporter_id)
            except CustomUser.DoesNotExist:
                 return Response({'reporter_id': 'Invalid reporter user ID provided.'}, status=status.HTTP_400_BAD_REQUEST)

            # Get files directly from request.FILES using keys from your React form
            identity_card_file = request.FILES.get('identityCard')
            person_photo_file = request.FILES.get('photos')

            # --- Validation: Check if required person_photo was sent ---
            # Make sure 'person_photo' is not blank/null in your model if required
            if not person_photo_file and not MissingPersonReport._meta.get_field('person_photo').blank:
                 return Response({'photos': 'Person photo is required.'}, status=status.HTTP_400_BAD_REQUEST)
            # --- End Validation ---

            # Create the report instance, passing files directly to CloudinaryFields
            report = MissingPersonReport.objects.create(
                reporter=reporter_user,
                identity_card_image=identity_card_file, # Pass file or None
                person_photo=person_photo_file,       # Pass file
                **serializer.validated_data # Pass other validated text fields
            )

            # Return response using the Detail serializer to show the created object
            output_serializer = MissingPersonReportDetailSerializer(report, context=self.get_serializer_context())
            headers = self.get_success_headers(output_serializer.data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error creating MissingPersonReport: {e}") # Basic logging
            # import traceback; traceback.print_exc() # Uncomment for detailed traceback
            return Response({'error':'An internal server error occurred during report creation.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Default methods handle:
    # list(): GET / (uses MissingPersonReportListSerializer)
    # retrieve(): GET /{pk}/ (uses MissingPersonReportDetailSerializer)
    # destroy(): DELETE /{pk}/ (deletes report)
    # update()/partial_update(): PUT/PATCH /{pk}/ (uses MissingPersonReportDetailSerializer by default,
    #                                            does NOT handle image updates well without overriding)

