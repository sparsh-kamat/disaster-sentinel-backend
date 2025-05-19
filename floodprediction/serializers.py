from rest_framework import serializers
from datetime import datetime


class FloodPredictionInputSerializer(serializers.Serializer):
    """
    Serializer for validating the input data for flood prediction.
    Matches the features expected by your SageMaker model.
    """
    prcp_cum3 = serializers.FloatField(required=True)
    prcp_lag1 = serializers.FloatField(required=True)
    sm_anomaly = serializers.FloatField(required=True)
    streamflow_lag1 = serializers.FloatField(required=True)
    streamflow_avg3 = serializers.FloatField(required=True)
    
    # Either 'doy' or 'date' should be provided.
    # 'date' will be preferred if both are present, and 'doy' will be calculated by SageMaker.
    doy = serializers.IntegerField(required=False, min_value=1, max_value=366)
    date = serializers.CharField(required=False, max_length=10) # Expects "YYYY-MM-DD"

    def validate_date(self, value):
        """
        Validate the date format if 'date' is provided.
        """
        if value: # Only validate if date is provided
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise serializers.ValidationError("Date must be in YYYY-MM-DD format.")
        return value

    def validate(self, data):
        """
        Check that either 'doy' or 'date' is provided.
        """
        if 'doy' not in data and 'date' not in data:
            raise serializers.ValidationError("Either 'doy' (day of year) or 'date' (YYYY-MM-DD) must be provided.")
        if not data.get('doy') and not data.get('date'): # Handles cases where they are empty strings
             raise serializers.ValidationError("Either 'doy' (day of year) or 'date' (YYYY-MM-DD) must not be empty if provided.")
        return data

    def to_sagemaker_payload(self):
        """
        Prepares the payload in the format expected by the SageMaker endpoint's inference script.
        Your inference script handles 'date' to 'doy' conversion.
        """
        validated_data = self.validated_data
        payload = {
            'prcp_cum3': validated_data['prcp_cum3'],
            'prcp_lag1': validated_data['prcp_lag1'],
            'sm_anomaly': validated_data['sm_anomaly'],
            'streamflow_lag1': validated_data['streamflow_lag1'],
            'streamflow_avg3': validated_data['streamflow_avg3'],
        }
        # Prefer 'date' if available, as the SageMaker inference script handles conversion to 'doy'
        if 'date' in validated_data and validated_data['date']:
            payload['date'] = validated_data['date']
        elif 'doy' in validated_data and validated_data['doy']:
            payload['doy'] = validated_data['doy']
        
        return payload
