==================
DeepSpeech Server
==================

.. image:: https://github.com/MainRo/deepspeech-server/actions/workflows/pythonpackage.yml/badge.svg
    :target: https://github.com/MainRo/deepspeech-server/actions/workflows/pythonpackage.yml

.. image:: https://badge.fury.io/py/deepspeech-server.svg
    :target: https://badge.fury.io/py/deepspeech-server

Key Features
============

This is an http server that can be used to test the Coqui STT project (the
successor of the Mozilla DeepSpeech project). You need an environment with
DeepSpeech or Coqui to run this server.

This code uses the Coqui STT 1.0 APIs.

Installation
=============

The server is available on pypi, so you can install it with pip:

.. code-block:: console

    pip3 install deepspeech-server


You can also install deepspeech server from sources:

.. code-block:: console

    python3 setup.py install

Note that python 3.6 is the minimum version required to run the server.

Starting the server
====================

.. code-block:: console

    deepspeech-server --config config.json

What is a STT model?
--------------------

The quality of the speech-to-text engine depends heavily on which models it
loads at runtime. Think of them as a sort of pattern that controls how the
engine works.

How to use a specific STT model
-------------------------------

You can use coqui without training a model. Pre-trained models are on
offer at the Coqui Model Zoo (Make sure the STT Models tab is selected):

https://coqui.ai/models

Once you've downloaded a pre-trained model, make a copy of the sample
configuration file. Edit the `"model"` and `"scorer"` fields in your new file
for the engine you want to use so that they match the downloaded files:

.. code-block:: console

    cp config.sample.json config.json
    $EDITOR config.json

Lastly, start the server:

.. code-block:: console

    deepspeech-server --config config.json

Server configuration
=====================

The configuration is done with a json file, provided with the "--config" argument.
Its structure is the following one:

.. code-block:: json

    {
      "coqui": {
        "model" :"coqui-1.0.tflite",
        "scorer" :"huge-vocabulary.scorer",
        "beam_width": 500
      },
      "server": {
        "http": {
          "host": "0.0.0.0",
          "port": 8080,
          "request_max_size": 1048576
        }
      },
      "log": {
        "level": [
          { "logger": "deepspeech_server", "level": "DEBUG"}
        ]
      }
    }

The configuration file contains several sections and sub-sections.

coqui section configuration
---------------------------

Section "coqui" contains configuration of the coqui-stt engine:

**model**: The model that was trained by coqui. Must be a tflite (TensorFlow Lite) file.

**scorer**: [Optional] The scorer file. Use this to tune the STT to understand certain phrases better.

**lm_aplha**: [Optional] alpha hyperparameter for the scorer.

**lm_beta**: [Optional] beta hyperparameter for the scorer.

**beam_width**: [Optional] The size of the beam search. Corresponds directly to how long decoding takes.

http section configuration
--------------------------

**request_max_size** (default value: 1048576, i.e. 1MiB) is the maximum payload
size allowed by the server. A received payload size above this threshold will
return a "413: Request Entity Too Large" error.

**host**  (default value: "0.0.0.0") is the listen address of the http server.

**port** (default value: 8080) is the listening port of the http server.

log section configuration
-------------------------

The log section can be used to set the log levels of the server. This section
contains a list of log entries. Each log entry contains the name of a **logger** 
and its **level**. Both follow the convention of the python logging module.


Using the server
================

Inference on the model is done via http post requests. For example with the
following curl command:

.. code-block:: console

     curl -X POST --data-binary @testfile.wav http://localhost:8080/stt
