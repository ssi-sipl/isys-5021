import joblib
import pandas as pd

model = joblib.load("classification_model.pkl")

def classification_pipeline(range,velocity,azimuth):
    new_data = pd.DataFrame({
        'range': [range],
        'velocity': [velocity],
        'azimuth': [azimuth]
    })
    
    predictions = model.predict(new_data)
    
    return predictions[0]

if __name__ == "__main__":
    classification_pipeline(88.3,-15.4, 0.13)
