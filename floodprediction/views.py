from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .generateSummary import generate_disaster_summary

class DisasterSummaryAPIView(APIView):
    def post(self, request, format=None):
        data = request.data
        required_fields = [
            'disaster_date',
            'month_occurred',
            'disaster_location',
            'disaster_type',
            'total_deaths',
            'total_injured',
            'total_affected'
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            summary = generate_disaster_summary(
                disaster_date=data['disaster_date'],
                month_occurred=data['month_occurred'],
                disaster_location=data['disaster_location'],
                disaster_type=data['disaster_type'],
                total_deaths=data['total_deaths'],
                total_injured=data['total_injured'],
                total_affected=data['total_affected']
            )
            return Response({"summary": summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
