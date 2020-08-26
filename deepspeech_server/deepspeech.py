import io
import logging
from collections import namedtuple

import rx
from cyclotron import Component
from cyclotron_std.logging import Log
from deepspeech import Model

import deepspeech_server.decoding as decoding


Sink = namedtuple('Sink', ['speech'])
Source = namedtuple('Source', ['text', 'log'])

# Sink events
Scorer = namedtuple('Scorer', ['scorer', 'lm_alpha', 'lm_beta'])
Scorer.__new__.__defaults__ = (None, None, None)

Initialize = namedtuple('Initialize', ['model', 'scorer', 'beam_width'])
Initialize.__new__.__defaults__ = (None,)

SpeechToText = namedtuple('SpeechToText', ['data', 'context'])

# Sourc eevents
TextResult = namedtuple('TextResult', ['text', 'context'])
TextError = namedtuple('TextError', ['error', 'context'])


def make_driver(loop=None):
    def driver(sink):
        model = None
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

        def setup_model(model_path, scorer, beam_width):
            log("creating model {} with scorer {}...".format(model_path, scorer))
            model = Model(model_path)

            if scorer.scorer is not None:
                model.enableExternalScorer(scorer.scorer)
                if scorer.lm_alpha is not None and scorer.lm_beta is not None:
                    if model.setScorerAlphaBeta(scorer.lm_alpha, scorer.lm_beta) != 0:
                        raise RuntimeError("Unable to set scorer parameters")

            if beam_width is not None:
                if model.setBeamWidth(beam_width) != 0:
                    raise RuntimeError("Unable to set beam width")

            log("model is ready.")
            return model

        def subscribe(observer, scheduler):
            def on_deepspeech_request(item):
                nonlocal model

                if type(item) is SpeechToText:
                    if model is not None:
                        try:
                            audio = decoding.decode_audio(io.BytesIO(item.data))
                            text = model.stt(audio)
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
                    model = setup_model(
                        item.model, item.scorer, item.beam_width)
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
