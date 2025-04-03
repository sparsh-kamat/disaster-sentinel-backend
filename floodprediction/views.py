from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .generateSummary import generate_disaster_summary
from .scrape_images import get_disaster_images
from .predict_flood import FloodPredictor


class FloodPredictionView(APIView):
    def post(self, request):
        # Load model and make prediction
        predictor = FloodPredictor()

        # Check for input data
        input_data = request.data
        prediction = predictor.predict(input_data)

        # Return response
        if 'error' in prediction:
            return Response(prediction, status=status.HTTP_400_BAD_REQUEST)
        return Response(prediction, status=status.HTTP_200_OK)
    
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


class DisasterImagesAPIView(APIView):
    def post(self, request, format=None):
        data = request.data
        required_fields = [
            'disaster_date',
            'month_occurred',
            'disaster_location',
            'disaster_type',
            'total_deaths',
            'total_injured',
            'total_affected',
            'disaster_state',
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            return Response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            query = f"{data['disaster_type']} disaster in {data['location']}, {data['disaster_state']}  during {data['month_occurred']} {data['disaster_date']} - destruction, damage, rescue operations, and aftermath"
            summary = get_disaster_images(
                query= query , num_images= 10
            )
            return Response({"summary": summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
