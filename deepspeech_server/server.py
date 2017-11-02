from rx.subjects import Subject

from collections import OrderedDict

from driver.http_driver import http_driver
from driver.console_driver import console_driver
from driver.deepspeech_driver import deepspeech_driver

def main(sources):
    stt = sources["HTTP"]["add_route"]("POST", "/stt")
    text = sources["DEEPSPEECH"]["text"]().share()

    http_response = text.map(lambda i: { "data": i["text"], "context": i["context"] })
    console = text.map(lambda i: i["text"])

    return OrderedDict([
        ("CONSOLE", console),
        ("DEEPSPEECH", stt),
        ("HTTP", http_response),
    ])


if __name__ == '__main__':

    http_proxy = Subject()
    console_proxy = Subject()
    deepspeech_proxy = Subject()

    sources = OrderedDict([
        ("DEEPSPEECH", deepspeech_driver(deepspeech_proxy)),
        ("HTTP", http_driver(http_proxy)),
        ("CONSOLE", console_driver(console_proxy)),
    ])


    sinks = main(sources)

    sinks["CONSOLE"].subscribe(console_proxy)
    sinks["DEEPSPEECH"].subscribe(deepspeech_proxy)
    sinks["HTTP"].subscribe(http_proxy)

    sources["HTTP"]["run"]()
    print("bar")
