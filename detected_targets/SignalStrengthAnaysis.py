import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

df0 = pd.read_json("./without_lid.json")
df2 = pd.read_json("./2mm.json")
df3 = pd.read_json("./3mm.json")
df4 = pd.read_json("./4mm.json")


signal_stats_0 = df0['signal_strength'].describe()
signal_stats_2 = df2['signal_strength'].describe()
signal_stats_3 = df3['signal_strength'].describe()
signal_stats_4 = df4['signal_strength'].describe()

def threshold_analysis(df):
    mean_strength = df['signal_strength'].mean()
    std_strength = df['signal_strength'].std()

    threshold_lower = mean_strength + 1 * std_strength

    # Threshold based on 75th and 85th percentiles
    threshold_75 = df['signal_strength'].quantile(0.75)
    threshold_85 = df['signal_strength'].quantile(0.85)

    # Compare results
    print(f"Mean + 1 * Std Threshold: {threshold_lower:.2f}")
    print(f"75th Percentile Threshold: {threshold_75:.2f}")
    print(f"85th Percentile Threshold: {threshold_85:.2f}")

    # Valid detections for each threshold
    for thresh in [threshold_lower, threshold_75, threshold_85]:
        valid_count = len(df[df['signal_strength'] > thresh])
        percentage = (valid_count / len(df)) * 100
        print(f"Threshold: {thresh:.2f} | Valid Detections: {valid_count} ({percentage:.2f}%)")

print("Signal Strength Statistics:")
print("-"*30)
print("(without lid):")
threshold_analysis(df0)
print("-"*30)
print("(2mm):")
threshold_analysis(df2)
print("-"*30)
print("(3mm):")
threshold_analysis(df3)
print("-"*30)
print("(4mm):")
threshold_analysis(df4)
print("-"*30)




