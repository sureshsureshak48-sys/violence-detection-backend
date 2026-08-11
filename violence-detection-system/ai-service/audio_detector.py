import os
import uuid
import subprocess

import librosa
import numpy as np


class AudioViolenceDetector:

    def __init__(self, model):

        self.model = model

        self.temp_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

    def detect(self, file_path):

        unique_id = str(uuid.uuid4())

        wav_path = os.path.join(
            self.temp_dir,
            f"audio_{unique_id}.wav"
        )

        try:

            command = [
                "ffmpeg",
                "-y",
                "-i",
                file_path,
                "-vn",
                "-ac",
                "1",
                "-ar",
                "22050",
                wav_path
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:

                raise Exception(
                    "Audio conversion failed"
                )

            audio, sample_rate = librosa.load(
                wav_path,
                sr=22050,
                mono=True
            )


            if len(audio) == 0:

                raise Exception(
                    "Audio file is empty"
                )
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=sample_rate,
                n_mfcc=13
            )

            features = np.mean(
                mfcc.T,
                axis=0
            )


            features = features.reshape(
                1,
                -1
            )

            prediction = self.model.predict(features)


            probabilities = self.model.predict_proba(features)
            print("Prediction:", prediction[0])
            print("Class labels:", self.model.classes_)
            print("Probabilities:", probabilities)

            result_label = str(prediction[0])


            return {
                "success": True,
                "result": result_label
            }


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


        finally:


            if os.path.exists(wav_path):

                try:

                    os.remove(wav_path)

                except Exception:

                    pass