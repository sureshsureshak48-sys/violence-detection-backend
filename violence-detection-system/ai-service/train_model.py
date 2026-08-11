import os
import librosa
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier


dataset_path = "../dataset"

features = []
labels = []


def extract_features(file_path):
    audio, sr = librosa.load(file_path, sr=22050)

    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=13
    )

    return np.mean(mfcc.T, axis=0)


# Read dataset
for label in ["normal","violence"]:

    folder = os.path.join(dataset_path, label)

    for file in os.listdir(folder):

        if file.endswith(".wav"):

            path = os.path.join(folder, file)

            feature = extract_features(path)

            features.append(feature)

            labels.append(label)



X = np.array(features)
y = np.array(labels)


print("Features shape:", X.shape)
print("Labels:", y)


# Train model
model = RandomForestClassifier()

model.fit(X, y)


os.makedirs("../models", exist_ok=True)

with open("../models/violence_model.pkl", "wb") as f:
    pickle.dump(model, f)


print("Model trained successfully!")
print("Saved: models/violence_model.pkl")