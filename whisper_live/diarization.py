# diarization should process the whole stream of audio every time since it relies on the previous results
# to make the current decision
from pyannote.audio import Pipeline
import torch
from intervaltree import Interval, IntervalTree


from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
HUGGINGFACE_ACCESS_TOKEN = os.environ["HUGGINGFACE_ACCESS_TOKEN"]


class Diarization():
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.0",
            use_auth_token=HUGGINGFACE_ACCESS_TOKEN)
        if torch.cuda.is_available():
            # if we GPU available, use it
            self.pipeline.to(torch.device("cuda"))

    def transform_diarization_output(self, diarization):
        l = []
        for segment, speaker in diarization.itertracks():
            l.append({"start": segment.start,
                     "end": segment.end, "speaker": speaker})
        return l

    def process(self, waveform, sample_rate):
        # convert samples to tensor
        audio_tensor = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)
        # run diarization model on tensor
        diarization = self.pipeline(
            {"waveform": audio_tensor, "sample_rate": sample_rate})
        # convert output to list of dicts
        diarization = self.transform_diarization_output(diarization)
        return diarization

    def join_transcript_with_diarization(self, transcript, diarization):
        
        diarization_tree = IntervalTree()
        # Add diarization to interval tree
        for dia in diarization:
            diarization_tree.addi(dia['start'], dia['end'], dia['speaker'])
        
        joined = []
        for seg in transcript:
            interval_start = seg['start']
            interval_end = seg['end']
            # Get overlapping diarization
            overlaps = diarization_tree[interval_start:interval_end]
            speakers = [overlap.data for overlap in overlaps]
            # Add to result
            joined.append({
                'start': interval_start,
                'end': interval_end,
                'speakers': speakers,
                'text': seg['text']
            })
        
        return joined
