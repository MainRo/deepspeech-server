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

# The alpha hyperparameter of the CTC decoder. Language Model weight
LM_WEIGHT = 1.75

# The beta hyperparameter of the CTC decoder. Word insertion weight (penalty)
WORD_COUNT_WEIGHT = 1.00

# Valid word insertion weight. This is used to lessen the word insertion penalty
# when the inserted word is part of the vocabulary
VALID_WORD_COUNT_WEIGHT = 1.00

def deepspeech_driver(sink):
    ds_model = None
    model_path = None
    alphabet_path = None
    text_observer = None
    lm_path = None
    trie_path = None

    def create_text_stream():
        def on_text_stream_subscribe(o):
            nonlocal text_observer
            text_observer = o

        text_observable = Observable.create(on_text_stream_subscribe)
        return text_observable

    def setup_model(model_path, alphabet, lm, trie):
        if model_path and alphabet:
            print("creating model {} {}".format(model_path, alphabet))
            ds_model = Model(model_path, N_FEATURES, N_CONTEXT, alphabet, BEAM_WIDTH)

            if lm and trie:
                ds_model.enableDecoderWithLM(alphabet, lm, trie, LM_WEIGHT,
                               WORD_COUNT_WEIGHT, VALID_WORD_COUNT_WEIGHT)
            return ds_model
        return None

    def on_deepspeech_request(item):
        nonlocal text_observer
        nonlocal ds_model
        nonlocal model_path
        nonlocal alphabet_path
        nonlocal lm_path
        nonlocal trie_path

        if item["what"] == "stt":
            if ds_model is not None:
                fs, audio = wav.read(io.BytesIO(item["data"]))
        #       convert to mono. todo: move to a component or just a function here
                if len(audio.shape) > 1:
                    audio = audio[:,0]
                text_observer.on_next({ "what": "text", "text": ds_model.stt(audio, fs), "context": item["context"]})
            # todo: send error

        elif item['what'] == "conf_complete":
            ds_model = setup_model(model_path, alphabet_path, lm_path, trie_path)
        elif item["what"] == "ds_conf_model":
            model_path = item["value"]
        elif item["what"] == "ds_conf_alphabet":
            alphabet_path = item["value"]
        elif item["what"] == "ds_conf_lm":
            lm_path = item["value"]
        elif item["what"] == "ds_conf_trie":
            trie_path = item["value"]

    sink.subscribe(lambda item: on_deepspeech_request(item))

    return {
        "text": create_text_stream
    }
