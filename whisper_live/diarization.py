# diarization should process the whole stream of audio every time since it relies on the previous results
# to make the current decision
from pyannote.audio import Pipeline
import torch


from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
HUGGINGFACE_ACCESS_TOKEN = os.environ["HUGGINGFACE_ACCESS_TOKEN"]


class Diarization():
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.0",
            use_auth_token=HUGGINGFACE_ACCESS_TOKEN)

    def process(self, waveform, sample_rate):
        # print('Waveform shape: ', waveform.shape)
        # print('Waveform: ', waveform)
        audio_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)
        # print('Audio tensor shape: ', audio_tensor.shape)
        # print('Audio tensor: ', audio_tensor)
        diarization = self.pipeline(
            {"waveform": audio_tensor, "sample_rate": sample_rate})
        return diarization
