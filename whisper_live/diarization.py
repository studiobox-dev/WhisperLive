# diarization should process the whole stream of audio every time since it relies on the previous results
# to make the current decision
from pyannote.audio import Pipeline
import torch
# from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
# from pyannote.audio import Audio
# from pyannote.core import Segment
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
HUGGINGFACE_ACCESS_TOKEN = os.environ["HF_ACCESS_TOKEN"]


class Diarization():
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.0",
            use_auth_token=HUGGINGFACE_ACCESS_TOKEN)

    def process(self, waveform, sample_rate):
        diarization = self.pipeling(
            {"waveform": waveform, "sample_rate": sample_rate})
        return diarization
