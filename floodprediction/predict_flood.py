# predict_flood.py
import joblib
import numpy as np
from pathlib import Path
from datetime import datetime

class FloodPredictor:
    def __init__(self, model_path=None):
        model_path = model_path or Path(__file__).parent/'models'/'flood_model.joblib'
        data = joblib.load(model_path)
        
        # Only unpack the 4 saved components
        self.model = data['model']
        self.features = data['features'] 
        self.threshold = data['threshold']
        self.needs_doy = data.get('doy_feature', False)

    def predict(self, input_data):
        # Convert date to doy if needed
        if self.needs_doy and 'date' in input_data:
            input_data['doy'] = datetime.strptime(input_data['date'], '%Y-%m-%d').timetuple().tm_yday
        
        # Validate input
        missing = set(self.features) - set(input_data.keys())
        if missing:
            return {'error': f'Missing features: {missing}'}
        
        # Prepare input array in EXACT same order as training
        X = np.array([[input_data[f] for f in self.features]])
        
        # Predict
        proba = self.model.predict_proba(X)[0][1]
        return {
            'probability': float(proba),
            'prediction': int(proba >= self.threshold),
            'threshold': self.threshold
        }

# Example usage
if __name__ == "__main__":
    predictor = FloodPredictor()
    print(predictor.predict({'prcp_cum3': 10.22, 'prcp_lag1': 2.11, 'sm_anomaly': 3.30, 'streamflow_lag1': 470.64, 'streamflow_avg3': 467.01, 'doy': 227.00}))