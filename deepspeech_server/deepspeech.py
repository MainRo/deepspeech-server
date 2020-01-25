import io
import logging
from collections import namedtuple
import scipy.io.wavfile as wav

import rx
from cyclotron import Component
from cyclotron_std.logging import Log
from deepspeech import Model


Sink = namedtuple('Sink', ['speech'])
Source = namedtuple('Source', ['text', 'log'])

# Sink events
FeaturesParameters = namedtuple('FeaturesParameters', ['beam_width', 'lm_alpha', 'lm_beta'])
FeaturesParameters.__new__.__defaults__ = (500, 0.75, 1.85)

Initialize = namedtuple('Initialize', ['model', 'lm', 'trie', 'features'])
SpeechToText = namedtuple('SpeechToText', ['data', 'context'])

# Sourc eevents
TextResult = namedtuple('TextResult', ['text', 'context'])
TextError = namedtuple('TextError', ['error', 'context'])


def make_driver(loop=None):
    def driver(sink):
        ds_model = None
        log_observer = None

        def on_log_subscribe(observer, scheduler):
            nonlocal log_observer
            log_observer = observer

        def log(message, level=logging.DEBUG):
            if log_observer is not None:
                log_observer.on_next(Log(
                    logger=__name__,
                    level=level,
                    message=message,
                ))

        def setup_model(model_path, lm, trie, features):
            log("creating model {} with features {}...".format(model_path, features))
            ds_model = Model(
                model_path,
                features.beam_width)

            if lm and trie:
                ds_model.enableDecoderWithLM(
                    lm, trie,
                    features.lm_alpha, features.lm_beta)
            log("model is ready.")
            return ds_model

        def subscribe(observer, scheduler):
            def on_deepspeech_request(item):
                nonlocal ds_model

                if type(item) is SpeechToText:
                    if ds_model is not None:
                        try:
                            _, audio = wav.read(io.BytesIO(item.data))
                            # convert to mono.
                            # todo: move to a component or just a function here
                            if len(audio.shape) > 1:
                                audio = audio[:, 0]
                            text = ds_model.stt(audio)
                            log("STT result: {}".format(text))
                            observer.on_next(rx.just(TextResult(
                                text=text,
                                context=item.context,
                            )))
                        except Exception as e:
                            log("STT error: {}".format(e), level=logging.ERROR)
                            observer.on_next(rx.throw(TextError(
                                error=e,
                                context=item.context,
                            )))
                elif type(item) is Initialize:
                    log("initialize: {}".format(item))
                    ds_model = setup_model(
                        item.model, item.lm, item.trie, item.features or FeaturesParameters())
                else:
                    log("unknown item: {}".format(item), level=logging.CRITICAL)
                    observer.on_error(
                        "Unknown item type: {}".format(type(item)))

            sink.speech.subscribe(lambda item: on_deepspeech_request(item))

        return Source(
            text=rx.create(subscribe),
            log=rx.create(on_log_subscribe),
        )

    return Component(call=driver, input=Sink)
