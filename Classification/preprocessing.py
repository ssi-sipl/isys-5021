import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

filename = "dataset.npy"

dataset = np.load(filename, allow_pickle=True)

class_name = ['vehicle', 'person', 'bicycle', 'uav']

custom_df = pd.DataFrame(columns=["range", "velocity", "azimuth", "class_name"])
secondary = 0
print("Iterating over ",len(dataset),"entries.")
for i in range(len(dataset)):
    if len(dataset[i]["range"]) == len(dataset[i]["velocity"]) == len(dataset[i]["azimuth"]):
        print("Processing Entry ",i," : ", len(dataset[i]["range"]), "entries")
        length = len(dataset[i]["range"])
        secondary+=length
        for j in range(length):
            custom_df.loc[len(custom_df)] = {
                "range": dataset[i]["range"][j],
                "velocity": dataset[i]["velocity"][j],
                "azimuth": dataset[i]["azimuth"][j],
                "class_name": dataset[i]["class_name"]
            }

print("-"*50)
print("Done Processing All Entries.")
print("-"*50)

print(custom_df.head())
print("-"*50)

print("Length of dataset: ", len(dataset))
print("Length of custom_df: ", len(custom_df))
print("-"*50)

custom_df.to_csv("custom_radar_classification_dataset.csv", index=False)