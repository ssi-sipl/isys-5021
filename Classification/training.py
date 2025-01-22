import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import shuffle
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

# Load dataset
data = pd.read_csv("custom_radar_classification_dataset.csv")
print("Dataset Loaded: ")
print(data.head())

# Feature scaling and label encoding
scaler = StandardScaler()
label_encoder = LabelEncoder()

x = data[["range", "velocity", "azimuth"]]  # Features
y = data["class_name"]  # Target/Label

x_scaled = scaler.fit_transform(x)
y_encoded = label_encoder.fit_transform(y)

# Shuffle the data
x, y = shuffle(x_scaled, y_encoded, random_state=42)
x, y = shuffle(x, y, random_state=56)
x, y = shuffle(x, y, random_state=78)
print("Shuffling Completed.")

# Split data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.7, random_state=42)
print("\nData Split Complete:")
print(f"Training Samples: {len(x_train)}, Testing Samples: {len(x_test)}")

# Random Forest Classifier with hyperparameter tuning
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [None, 10, 20, 30, 40],
    "min_samples_split": [2, 5, 10, 15],
    "min_samples_leaf": [1, 2, 4, 8],
    "max_features": ["sqrt", "log2", None],
    "bootstrap": [True, False],
}

grid_search = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42, class_weight="balanced"),
    param_grid=param_grid,
    cv=5,
    scoring="accuracy",
    verbose=2,
    n_jobs=-1,
)

grid_search.fit(x_train, y_train)
print("Best Parameters:", grid_search.best_params_)

# Save the best model and preprocessing objects
best_model = grid_search.best_estimator_
joblib.dump(best_model, "classification_model_2.pkl")
print("\nModel Saved as classification_model_2.pkl")

joblib.dump(scaler, "scaler.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print("Scaler and Label Encoder Saved.")

# Evaluate the model
y_pred = best_model.predict(x_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
