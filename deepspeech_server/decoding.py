"""
Audio decoding module.
"""

from typing import BinaryIO, List
import logging

import scipy.io.wavfile as wav


def audio_to_array_pyav(file: BinaryIO) -> np.array:
    """
    Resample the input audio to the format that DeepSpeech expects.

    This one uses PyAV.

    :returns: A 1-dimensional NumPy array.
    """
    resampler = av.audio.resampler.AudioResampler(
        format="s16p", layout="mono", rate=16000
    )  # FIXME: For some reason, the resampler needs to be redefined everytime. Otherwise, you'd get errors like "ValueError: Input frame pts 0 != expected 31600; fix or set to None.".
    audio = av.open(file)
    frames: List[av.frame.Frame] = []
    for frame in audio.decode(
        audio=0
    ):  # TODO: What about when there is more than 1 channel?
        frames.append(resampler.resample(frame).to_ndarray())
    return np.concatenate(frames, axis=1).flatten()


def audio_to_array_scipy(file: BinaryIO) -> np.array:
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
    import numpy as np
except ImportError as e:
    logging.warning("Either PyAV or NumPy was not found. Falling back to SciPy...")
    audio_to_array = audio_to_array_scipy
else:
    # We have PyAV!
    audio_to_array = audio_to_array_pyav

__all__ = ("audio_to_array",)
