"""
Audio decoding module.
"""

import logging

import scipy.io.wavfile as wav
import numpy as np


def decode_audio_pyav(file):
    """
    Resample the input audio to the format that DeepSpeech expects.

    This one uses PyAV.

    :returns: A 1-dimensional NumPy array.
    """

    audio = av.open(file)
    if len(audio.streams.audio) > 1:
        logging.warning("Audio has more than one stream. Only one of them will be used.")

    resampler = av.audio.resampler.AudioResampler(
        format="s16", layout="mono", rate=16000
    )
    resampled_frames = []
    for frame in audio.decode(audio=0):
        # As of PyAV 9.0, one input frame may be resampled to multiple outputs.
        # Convert each into a numpy ndarray...
        iterable_frames = map(lambda f:f.to_ndarray(), resampler.resample(frame))
        # ...then flatten each of those arrays down to 1D
        flat_frames = list(map(lambda f:f.flatten(), iterable_frames))
        # Add all of the resampled frames to our output list
        resampled_frames.extend(flat_frames)

    return np.concatenate(resampled_frames)


def decode_audio_scipy(file):
    """
    Resample the input audio to the format that DeepSpeech expects.

    This one uses SciPy.

    :returns: A 1-dimensional NumPy array.
    """
    _, audio = wav.read(file)
    # convert to mono.
    # todo: move to a component or just a function here
    if len(audio.shape) > 1:
        audio = audio[:, 0]
    return audio


try:
    import av
except ImportError as e:
    logging.warning("PyAV was not found. Falling back to SciPy...")
    decode_audio = decode_audio_scipy
else:
    logging.debug("Found PyAV!")
    decode_audio = decode_audio_pyav

__all__ = ("decode_audio",)
