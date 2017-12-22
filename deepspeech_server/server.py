import json
from rx import Observable
from rx.subjects import Subject

from collections import OrderedDict

from deepspeech_server.driver.file_reader_driver import file_reader_driver
from deepspeech_server.driver.http_driver import http_driver
from deepspeech_server.driver.console_driver import console_driver
from deepspeech_server.driver.deepspeech_driver import deepspeech_driver
from deepspeech_server.driver.arg_driver import arg_driver


def parse_config(config_data):
    ''' takes a stream with the content of the configuration file as input
    and returns a (hot) stream of arguments .

    deepspeech arguments: ds_conf_model, ds_conf_alphabet, ds_conf_trie, ds_conf_lm
    http server arguments: request_max_size
    '''
    def json_to_args(config):
        args = []
        if "deepspeech" in config:
            for arg in ["model", "alphabet", "lm", "trie"]:
                if arg in config["deepspeech"]:
                    args.append({
                        "what": "ds_conf_" + arg,
                        "value": config["deepspeech"][arg]
                    })

        if "server" in config:
            if "http" in config["server"]:
                for arg in ["request_max_size", "host", "port"]:
                    if arg in config["server"]["http"]:
                        args.append({
                            "what": "srv_http_conf_" + arg,
                            "value": config["server"]["http"][arg]
                        })

        args.append({"what": "conf_complete"})
        return Observable.from_(args)

    config = config_data \
        .filter(lambda i: i["name"] == "config") \
        .map(lambda i: json.loads(i["data"])) \
        .flat_map(json_to_args)

    return config.share()


def daemon_main(sources):
    args = sources["ARG"]["arguments"]()
    stt = sources["HTTP"]["request"]()
    text = sources["DEEPSPEECH"]["text"]().share()
    config_data = sources["FILE"]["data"]("config")

    arg_specs = Observable.from_([
        {"what": "argument", "arg_name": "config", "arg_help": "Path of the server configuration file"},
    ])

    config_file = args \
        .filter(lambda i: i["name"] == "config") \
        .map(lambda i: {"name": "config", "path": i["value"]})
    config = parse_config(config_data)

    ds_stt = stt \
        .map(lambda i: {"what": "stt", "data": i["data"], "context": i["context"]})
    ds_arg = config \
        .filter(lambda i: i["what"] in [
            "ds_conf_model", "ds_conf_alphabet",
            "ds_conf_trie", "ds_conf_lm",
            "conf_complete"])
    ds = ds_stt.merge(ds_arg)

    http_arg = config \
        .filter(lambda i: i["what"] in [
            "srv_http_conf_request_max_size",
            "srv_http_conf_host",
            "srv_http_conf_port",
            "conf_complete"])
    http_response = text \
        .map(lambda i: {"what": "response", "data": i["text"], "context": i["context"]})
    http_stt_route = Observable.from_([
        {"what": "add_route", "type": "POST", "path": "/stt"}
    ])
    http_init = Observable.concat([http_arg, http_stt_route])
    http = http_response.merge(http_init)

    console = text.map(lambda i: i["text"])

    return OrderedDict([
        ("ARG", arg_specs),
        ("FILE", config_file),
        ("CONSOLE", console),
        ("DEEPSPEECH", ds),
        ("HTTP", http),
    ])

def main():
    # todo: create a cycle runner
    arg_proxy = Subject()
    file_proxy = Subject()
    http_proxy = Subject()
    console_proxy = Subject()
    deepspeech_proxy = Subject()

    sources = OrderedDict([
        ("ARG", arg_driver(arg_proxy)),
        ("FILE", file_reader_driver(file_proxy)),
        ("DEEPSPEECH", deepspeech_driver(deepspeech_proxy)),
        ("HTTP", http_driver(http_proxy)),
        ("CONSOLE", console_driver(console_proxy)),
    ])

    sinks = daemon_main(sources)

    sinks["CONSOLE"].subscribe(console_proxy)
    sinks["DEEPSPEECH"].subscribe(deepspeech_proxy)
    sinks["HTTP"].subscribe(http_proxy)
    sinks["FILE"].subscribe(file_proxy)
    sinks["ARG"].subscribe(arg_proxy)

    sources["HTTP"]["run"]()


if __name__ == '__main__':
    main()
