from rx import Observable
from rx.subjects import Subject

from collections import OrderedDict

from deepspeech_server.driver.http_driver import http_driver
from deepspeech_server.driver.console_driver import console_driver
from deepspeech_server.driver.deepspeech_driver import deepspeech_driver
from deepspeech_server.driver.arg_driver import arg_driver


def daemon_main(sources):
    arg_values = sources["ARG"]["arguments"]()
    stt = sources["HTTP"]["add_route"]("POST", "/stt")
    text = sources["DEEPSPEECH"]["text"]().share()

    arg = Observable.from_([
        {"what": "argument", "arg_name": "model", "arg_help": "Path of the deepspeech model to use"},
        {"what": "argument", "arg_name": "alphabet", "arg_help": "Path of the alphabet file to use"}
    ])

    ds_stt = stt \
        .map(lambda i: {"what": "stt", "data": i["data"], "context": i["context"]})
    ds_arg = arg_values \
        .filter(lambda i: i["name"] == "model" or i["name"] == "alphabet") \
        .map(lambda i: {"what": i["name"], "value": i["value"]})
    ds = ds_stt.merge(ds_arg)

    http_response = text \
        .map(lambda i: {"data": i["text"], "context": i["context"]})
    console = text.map(lambda i: i["text"])

    return OrderedDict([
        ("ARG", arg),
        ("CONSOLE", console),
        ("DEEPSPEECH", ds),
        ("HTTP", http_response),
    ])

def main():
    # todo: create a cycle runner
    arg_proxy = Subject()
    http_proxy = Subject()
    console_proxy = Subject()
    deepspeech_proxy = Subject()

    sources = OrderedDict([
        ("ARG", arg_driver(arg_proxy)),
        ("DEEPSPEECH", deepspeech_driver(deepspeech_proxy)),
        ("HTTP", http_driver(http_proxy)),
        ("CONSOLE", console_driver(console_proxy)),
    ])

    sinks = daemon_main(sources)

    sinks["CONSOLE"].subscribe(console_proxy)
    sinks["DEEPSPEECH"].subscribe(deepspeech_proxy)
    sinks["HTTP"].subscribe(http_proxy)
    sinks["ARG"].subscribe(arg_proxy)

    sources["HTTP"]["run"]()


if __name__ == '__main__':
    main()
