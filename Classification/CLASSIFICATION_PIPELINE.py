import joblib
import pandas as pd
import numpy as np

model = joblib.load("Classification/classification_model.pkl")

def classification_pipeline(range,velocity,azimuth):
    new_data = pd.DataFrame({
        'range': [range],
        'velocity': [velocity],
        'azimuth': [azimuth]
    })
    
    predictions = model.predict(new_data)
    
    return predictions[0]

if __name__ == "__main__":
    print(classification_pipeline(123,50, 12))
