from rx import Observable
import argparse


def arg_driver(sink):
    parser = argparse.ArgumentParser()
    argument_observer = None

    def create_argument_stream():
        def on_subscribe(o):
            nonlocal argument_observer
            argument_observer=o

        return Observable.create(on_subscribe).share()

    def on_item(parser, item):
        if item["what"] == "argument":
            parser.add_argument("--" + item["arg_name"], help=item["arg_help"], required=True)
        return

    def on_completed(parser):
        nonlocal argument_observer
        args = parser.parse_args()
        if argument_observer != None:
            for key,value in vars(args).items():
                argument_observer.on_next({"name": key, "value": value})
        return

    sink.subscribe(
        on_next=lambda i: on_item(parser, i),
        on_completed=lambda: on_completed(parser))

    return {
        "arguments": create_argument_stream
    }
