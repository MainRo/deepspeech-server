from __future__ import absolute_import, division, print_function

import scipy.io.wavfile as wav
from deepspeech.model import Model
import io

from rx import Observable

model_file = "/media/Develop/datalab/moz-deep-speech/train-kelly/export/output_graph.pb"
alphabet = "/media/Develop/datalab/moz-deep-speech/DeepSpeech/data/alphabet.txt"
text_observer = None

def deepspeech_driver(sink):
    ds = Model(model_file, 26, 9, alphabet)

    def create_text_stream():
        def on_text_stream_subscribe(o):
            global text_observer
            text_observer = o

        text_observable = Observable.create(on_text_stream_subscribe)
        return text_observable

    def on_deepspeech_request(item):
        fs, audio = wav.read(io.BytesIO(item["data"]))
#       convert to mono. todo: move to a component or just a function here        
        if len(audio.shape) > 1:
            audio = audio[:,0]
        text_observer.on_next({ "what": "text", "text": ds.stt(audio, fs), "context": item["context"]})

    sink.subscribe(lambda item: on_deepspeech_request(item))

    return {
        "text": create_text_stream
    }
