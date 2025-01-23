import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import Callback, ReduceLROnPlateau, EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import joblib

# Load the data
data = pd.read_csv('custom_radar_classification_dataset.csv')

# Features and target
X = data[['range', 'velocity', 'azimuth']].values
y = data['class_name']

# Convert target labels to one-hot encoding
y = pd.get_dummies(y).values

class_names = pd.get_dummies(data['class_name']).columns.tolist()

# Save the class name mapping (index: class_name)
class_mapping = {index: label for index, label in enumerate(class_names)}
print("Class Mappings: ")
print(class_mapping)

# Save the mapping to a file
with open('class_mapping.txt', 'w') as f:
    for index, label in class_mapping.items():
        f.write(f"{index}:{label}\n")

# Split data into training, validation, and test sets
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Normalize the features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_test = scaler.transform(X_test)

# Save the scaler
joblib.dump(scaler, 'scaler.pkl')

# Define the enhanced neural network model
model = Sequential([
    Dense(128, activation='relu', input_shape=(3,), kernel_regularizer=l2(0.001)),  # Increased number of units
    Dropout(0.3),
    Dense(128, activation='relu', kernel_regularizer=l2(0.001)),  # Added another hidden layer
    Dropout(0.3),
    Dense(64, activation='relu', kernel_regularizer=l2(0.001)),  # Additional hidden layer
    Dropout(0.3),
    Dense(y.shape[1], activation='softmax')  # Output layer with softmax
])

# Compile the model with Adam optimizer and learning rate decay
optimizer = Adam(learning_rate=0.0005)
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

# Custom callback for real-time loss plot
class RealTimePlotCallback(Callback):
    def __init__(self):
        super().__init__()
        self.epochs = []
        self.losses = []
        self.val_losses = []
        self.accuracies = []
        self.val_accuracies = []
        plt.ion()  # Enable interactive mode
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line1, = self.ax.plot([], [], label='Training Loss', color='blue')
        self.line2, = self.ax.plot([], [], label='Validation Loss', color='orange')
        self.line3, = self.ax.plot([], [], label='Training Accuracy', color='green')
        self.line4, = self.ax.plot([], [], label='Validation Accuracy', color='red')
        self.ax.set_title("Real-Time Training and Validation Loss/Accuracy")
        self.ax.set_xlabel("Epochs")
        self.ax.set_ylabel("Metrics")
        self.ax.legend()
        self.ax.grid(True)

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        self.epochs.append(epoch)
        self.losses.append(logs.get('loss'))
        self.val_losses.append(logs.get('val_loss'))
        self.accuracies.append(logs.get('accuracy'))
        self.val_accuracies.append(logs.get('val_accuracy'))

        self.line1.set_data(self.epochs, self.losses)
        self.line2.set_data(self.epochs, self.val_losses)
        self.line3.set_data(self.epochs, self.accuracies)
        self.line4.set_data(self.epochs, self.val_accuracies)
        self.ax.relim()
        self.ax.autoscale_view()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def on_train_end(self, logs=None):
        plt.ioff()  # Turn off interactive mode
        plt.show()

# Instantiate the callback
real_time_plot = RealTimePlotCallback()

# Callbacks for learning rate decay and early stopping
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, verbose=1)
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train the model with callbacks
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    callbacks=[real_time_plot, reduce_lr, early_stopping]
)

# Evaluate the model on the test set
test_loss, test_accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {test_accuracy * 100:.2f}%")

# Save the trained model
model.save('classification_model.h5')

# Generate a classification report
y_pred = model.predict(X_test)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true_classes = np.argmax(y_test, axis=1)
print("\nClassification Report:\n")
print(classification_report(y_true_classes, y_pred_classes))
