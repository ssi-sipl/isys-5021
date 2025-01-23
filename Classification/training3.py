import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
import lightgbm as lgb
import joblib

# Load the dataset
file_path = 'custom_radar_classification_dataset.csv'  # Replace with your dataset path
radar_data = pd.read_csv(file_path)

# Encode the class_name column
label_encoder = LabelEncoder()
radar_data['class_label'] = label_encoder.fit_transform(radar_data['class_name'])

# Select features and target variable
X = radar_data[['range', 'velocity', 'azimuth']]
y = radar_data['class_label']

# Normalize the feature set
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# Apply SMOTE to the training data
smote = SMOTE(random_state=42)
X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)

# Prepare LightGBM datasets
lgb_train = lgb.Dataset(X_train_smote, label=y_train_smote)
lgb_test = lgb.Dataset(X_test, label=y_test)

# Define parameters for LightGBM
params = {
    'objective': 'multiclass',
    'num_class': len(label_encoder.classes_),
    'metric': 'multi_logloss',
    'boosting_type': 'gbdt',
    'learning_rate': 0.1,
    'num_leaves': 31,
    'max_depth': -1,
    'min_data_in_leaf': 20,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbosity': -1,
    'seed': 42
}

# Train the LightGBM model
num_boost_round = 100
early_stopping_rounds = 10

lgb_model = lgb.train(
    params,
    lgb_train,
    num_boost_round=num_boost_round,
    valid_sets=[lgb_train, lgb_test],  # Specify training and validation sets
    valid_names=['train', 'valid'],   # Optional: names for datasets
    early_stopping_rounds=early_stopping_rounds,
    verbose_eval=10
)

# Predict on the test set
y_pred = lgb_model.predict(X_test)
y_pred_labels = y_pred.argmax(axis=1)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred_labels)
classification_report_result = classification_report(
    y_test, y_pred_labels, target_names=label_encoder.classes_
)

# Print results
print("Accuracy:", accuracy)
print("Classification Report:\n", classification_report_result)

# Save the model, scaler, and label encoder
lgb_model.save_model("lgb_model.txt")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print("\nModel, Scaler, and Label Encoder Saved.")
