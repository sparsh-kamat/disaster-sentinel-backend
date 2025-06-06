from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .generateSummary import generate_disaster_summary
from .scrape_images import get_disaster_images
import boto3
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FloodPredictionInputSerializer


class FloodPredictionAPIView(APIView):
    """
    API View to handle flood prediction requests.
    It takes input features, calls the SageMaker endpoint, and returns the prediction.
    """
    def post(self, request, *args, **kwargs):
        serializer = FloodPredictionInputSerializer(data=request.data)
        if serializer.is_valid():
            sagemaker_payload = serializer.to_sagemaker_payload()

            try:
                # Initialize Boto3 SageMaker runtime client
                # Ensure your Django environment has AWS credentials configured
                # (e.g., via IAM role if on EC2/ECS, or AWS CLI config/env vars locally)
                client = boto3.client(
                    'sagemaker-runtime',
                    region_name=settings.SAGEMAKER_AWS_REGION
                )

                # Invoke the SageMaker endpoint
                response = client.invoke_endpoint(
                    EndpointName=settings.SAGEMAKER_ENDPOINT_NAME,
                    ContentType='application/json',
                    Accept='application/json',
                    Body=json.dumps(sagemaker_payload)
                )

                # Read and parse the response from SageMaker
                response_body_str = response['Body'].read().decode('utf-8')
                prediction_result = json.loads(response_body_str)

                # Check if SageMaker returned an error within its response
                if 'error' in prediction_result: # Based on your inference.py error handling
                    return Response(
                        {"sagemaker_error": prediction_result['error']},
                        status=status.HTTP_400_BAD_REQUEST # Or another appropriate status
                    )
                
                return Response(prediction_result, status=status.HTTP_200_OK)

            except boto3.exceptions.Boto3Error as e:
                # Catch Boto3 specific errors (credentials, service not found, etc.)
                # Log the error for debugging: print(f"Boto3 Error: {e}")
                return Response(
                    {"error": "Could not connect to the prediction service (Boto3 Error)."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as e:
                # Catch any other unexpected errors during the process
                # Log the error for debugging: print(f"Unexpected Error: {e}")
                return Response(
                    {"error": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Input data failed validation by the serializer
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
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
            query = f"{data['disaster_type']} disaster in {data['disaster_location']}, {data['disaster_state']}  during {data['month_occurred']} {data['disaster_date']} - destruction, damage, rescue operations, and aftermath"
            summary = get_disaster_images(
                query= query , num_images= 10
            )
            return Response({"summary": summary}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
