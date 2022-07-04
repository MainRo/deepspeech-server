==================
DeepSpeech Server
==================

.. image:: https://travis-ci.org/MainRo/deepspeech-server.svg?branch=master
    :target: https://travis-ci.org/MainRo/deepspeech-server

.. image:: https://badge.fury.io/py/deepspeech-server.svg
    :target: https://badge.fury.io/py/deepspeech-server

Key Features
============

This is an http server that can be used to test the Mozilla DeepSpeech project
or its successor, the Coqui STT project. You need an environment with
DeepSpeech or Coqui to run this server.

This code uses the DeepSpeech 0.7 APIs and Coqui STT 1.0 APIs.

Installation
=============

Before starting, you'll need to choose an engine.

Option A: Installing DeepSpeech
-------------------------------

First, install `deepspeech`. Depending on your system you can use the CPU
package:

.. code-block:: console

    pip3 install deepspeech

Or the GPU package:

.. code-block:: console

    pip3 install deepspeech-gpu

Option B: Installing Coqui STT
------------------------------

First, install `stt` (published by Coqui). There is only one package available,
but not to worry - it supports both CPU-bound and GPU environments:

.. code-block:: console

   pip3 install stt

Installing deepspeech-server
----------------------------

Then you can install the deepspeech server:

.. code-block:: console

    python3 setup.py install

The server is also available on pypi, so you can install it with pip:

.. code-block:: console

    pip3 install deepspeech-server

Note that python 3.5 is the minimum version required to run the server.

Starting the server
====================

.. code-block:: console

    deepspeech-server --config config.json

What is a STT model?
--------------------

The quality of the speech-to-text engine depends heavily on which models it
loads at runtime. Think of them as a sort of pattern that controls how the
engine works.

Coqui and deepspeech models both run on tensorflow, but the way they are built
means that the models for one cannot be used for the other. Note that the files
used for vocabulary (the so-called scorers) ARE compatible. Refer to the below
table:

.. csv-table:: Supported Formats
   :header: "Name", "Extension", "Engine Support"

   "Protobuf", "`.pb`", "Deepspeech"
   "Memory-mapped Protobuf", "`.pbmm`", "DeepSpeech"
   "TensorFlow Lite", "`.tflite`", "DeepSpeech, Coqui STT"
   "Scorer", "`.scorer`", "DeepSpeech, Coqui STT"

How to use a specific STT model
-------------------------------

You can use deepspeech without training a model yourself. Pre-trained
models are provided by Mozilla in the release page of the project (See the
assets section of the release note):

https://github.com/mozilla/DeepSpeech/releases

You can also use coqui without training a model. Pre-trained models are on
offer at the Coqui Model Zoo (Make sure the STT Models tab is selected):

https://coqui.ai/models

Once you've downloaded a pre-trained model, make a copy of the sample
configuration file. Edit the `"model"` and `"scorer"` fields in your new file
for the engine you want to use so that they match the downloaded files:

.. code-block:: console

    cp config.sample.json config.json
    $EDITOR config.json

Here's what to change if you want to use the models from deepspeech 0.9.3:

.. code-block:: json

     "deepspeech": {
       "model" :"/path/to/my/downloaded/models/deepspeech-0.9.3-models.pbmm",
       "scorer" :"/path/to/my/downloaded/models/deepspeech-0.9.3-models.scorer"
     },

Lastly, start the server in the usual way:

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
      "deepspeech": {
        "model" :"deepspeech-0.7.1-models.pbmm",
        "scorer" :"deepspeech-0.7.1-models.scorer",
        "beam_width": 500,
        "lm_alpha": 0.931289039105002,
        "lm_beta": 1.1834137581510284
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

**scorer**: [Optional] The scorer file. Use this to tune the STT to understand certain phrases better

**beam_width**: [Optional] The size of the beam search. Corresponds directly to how long decoding takes

deepspeech section configuration
--------------------------------

Section "deepspeech" contains configuration of the deepspeech engine:

**model**: The model that was generated by deepspeech. Can be a protobuf file or a memory mapped protobuf.

**scorer**: [Optional] The scorer file. The scorer is necessary to set lm_alpha or lm_beta manually

**beam_width**: [Optional] The size of the beam search

**lm_alpha** and **lm_beta**: [Optional] The hyperparmeters of the scorer

Section "server" contains configuration of the access part, with on subsection per protocol:

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
