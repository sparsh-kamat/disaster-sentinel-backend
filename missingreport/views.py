# missingreport/views.py

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import MissingPersonReport
from users.models import CustomUser

from .serializers import (
    MissingPersonReportCreateSerializer,
    MissingPersonReportListSerializer,
    MissingPersonReportDetailSerializer
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
