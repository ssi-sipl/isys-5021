import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, ConfusionMatrixDisplay
from sklearn.utils import shuffle
from sklearn.tree import plot_tree
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv("custom_radar_classification_dataset.csv")
print("Dataset Loaded: ")
print(data.head())


x = data[["range", "velocity", "azimuth"]]  # Features
y = data["class_name"]  # Target/Label

x, y = shuffle(x, y, random_state=42)
x, y = shuffle(x, y, random_state=56)
x, y = shuffle(x, y, random_state=78)
print("Shuffling Completed.")

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.5, random_state=42)
print("\nData Split Complete:")
print(f"Training Samples: {len(x_train)}, Testing Samples: {len(x_test)}")

clf = RandomForestClassifier(random_state=42)

param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [None, 10, 20, 30],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
}

grid_search = GridSearchCV(estimator=clf, param_grid=param_grid, cv=3, scoring="accuracy", verbose=2, n_jobs=-1)
grid_search.fit(x_train, y_train)
print("Best Parameters:", grid_search.best_params_)
best_model = grid_search.best_estimator_
y_pred = best_model.predict(x_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

joblib.dump(best_model, "classification_model_2.pkl")
print("\nModel Saved as classification_model_2.pkl")

# --- Visualization ---

# Confusion Matrix
cm_display = ConfusionMatrixDisplay.from_estimator(best_model, x_test, y_test, display_labels=best_model.classes_, cmap='Blues', values_format='d')
plt.title("Confusion Matrix")
plt.savefig("confusion_matrix.png")  # Save the figure
plt.show()

# Classification Report as Heatmap
report = classification_report(y_test, y_pred, output_dict=True)
report_df = pd.DataFrame(report).transpose()

plt.figure(figsize=(10, 6))
sns.heatmap(report_df.iloc[:-1, :-1], annot=True, cmap="YlGnBu", fmt=".2f")
plt.title("Classification Report")
plt.savefig("classification_report_heatmap.png")  # Save the figure
plt.show()

# Visualize a Decision Tree
plt.figure(figsize=(20, 10))
plot_tree(best_model.estimators_[0], feature_names=["range", "velocity", "azimuth"], class_names=best_model.classes_, filled=True)
plt.title("Visualization of a Decision Tree")
plt.savefig("decision_tree.png")  # Save the figure
plt.show()

