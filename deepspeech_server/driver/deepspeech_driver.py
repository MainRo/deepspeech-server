import io
import scipy.io.wavfile as wav

from rx import Observable
from deepspeech.model import Model

# Number of MFCC features to use
N_FEATURES = 26

# Size of the context window used for producing timesteps in the input vector
N_CONTEXT = 9

# Beam width used in the CTC decoder when building candidate transcriptions
BEAM_WIDTH = 500

def deepspeech_driver(sink):
    ds_model = None
    model_path = None
    alphabet_path = None
    text_observer = None

    def create_text_stream():
        def on_text_stream_subscribe(o):
            nonlocal text_observer
            text_observer = o

        text_observable = Observable.create(on_text_stream_subscribe)
        return text_observable

    def setup_model(model_path, alphabet):
        if model_path is not None and alphabet is not None:
            print("creating model {} {}".format(model_path, alphabet))
            return Model(model_path, N_FEATURES, N_CONTEXT, alphabet, BEAM_WIDTH)
        return None

    def on_deepspeech_request(item):
        nonlocal text_observer
        nonlocal ds_model
        nonlocal model_path
        nonlocal alphabet_path

        if item["what"] == "stt":
            fs, audio = wav.read(io.BytesIO(item["data"]))
    #       convert to mono. todo: move to a component or just a function here
            if len(audio.shape) > 1:
                audio = audio[:,0]
            text_observer.on_next({ "what": "text", "text": ds_model.stt(audio, fs), "context": item["context"]})

        elif item["what"] == "model":
            model_path = item["value"]
            ds_model = setup_model(model_path, alphabet_path)

        elif item["what"] == "alphabet":
            alphabet_path = item["value"]
            ds_model = setup_model(model_path, alphabet_path)

    sink.subscribe(lambda item: on_deepspeech_request(item))

    return {
        "text": create_text_stream
    }
