import json
from collections import namedtuple
from rx import Observable

from cyclotron import Component
from cyclotron.router import make_error_router

from cyclotron_aio.runner import run
import cyclotron_aio.httpd as httpd
import cyclotron_std.sys.argv as argv
import cyclotron_std.sys.stdout as stdout
import cyclotron_std.io.file as file
import cyclotron_std.argparse as argparse

import deepspeech_server.deepspeech as deepspeech


DeepspeechSink = namedtuple('DeepspeechSink', [
    'deepspeech', 'httpd', 'file', 'stdout'
])
DeepspeechSource = namedtuple('DeepspeechSource', [
    'deepspeech', 'httpd', 'file', 'argv'
])
DeepspeechDrivers = namedtuple('DeepspeechServerDrivers', [
    'deepspeech', 'httpd', 'file', 'argv', 'stdout'
])


def parse_config(config_data):
    ''' takes a stream with the content of the configuration file as input
    and returns a (hot) stream of arguments .
    '''
    config = config_data \
        .filter(lambda i: i.id == "config") \
        .flat_map(lambda i: i.data) \
        .do_action(lambda i: print("item: {}".format(i))) \
        .map(lambda i: json.loads(
            i,
            object_hook=lambda d: namedtuple('x', d.keys())(*d.values())))

    return config.share()


def deepspeech_server(sources):
    argv = sources.argv.argv
    stt = sources.httpd.route
    stt_response = sources.deepspeech.text.share()
    config_data = sources.file.response

    http_ds_error, route_ds_error = make_error_router()

    args = argparse.argparse(
        Observable.just(argparse.Parser(description="deepspeech server")),
        Observable.from_([
            argparse.AddArgument(
                name='--config', help="Path of the server configuration file")
        ]),
        argv.skip(1)
    )

    config_file = (
        args
        .filter(lambda i: i.key == 'config')
        .map(lambda i: file.Read(id='config', path=i.value))
    )
    config = parse_config(config_data)

    ds_stt = (
        stt
        .flat_map(lambda i: i.request)
        .map(lambda i: deepspeech.SpeechToText(data=i.data, context=i.context))
    )

    ds_arg = (
        config
        .map(lambda i: deepspeech.Initialize(
            model=i.deepspeech.model,
            alphabet=i.deepspeech.alphabet,
            lm=i.deepspeech.lm,
            trie=i.deepspeech.trie))
    )
    ds = ds_stt.merge(ds_arg)

    http_init = (
        config
        .flat_map(lambda i: Observable.from_([
            httpd.Initialize(request_max_size=i.server.http.request_max_size),
            httpd.AddRoute(
                methods=['POST'],
                path='/stt',
                id='stt',
            ),
            httpd.StartServer(
                host=i.server.http.host,
                port=i.server.http.port),
        ]))
    )

    http_response = (
        stt_response
        .let(route_ds_error,
            error_map=lambda e: httpd.Response(
                data="Speech to text error".encode('utf-8'),
                context=e.args[0].context,
                status=500
        ))
        .map(lambda i: httpd.Response(
            data=i.text.encode('utf-8'),
            context=i.context,
        ))
    )

    http = Observable.merge(http_init, http_response, http_ds_error)

    console = Observable.empty()

    return DeepspeechSink(
        file=file.Sink(request=config_file),
        stdout=stdout.Sink(data=console),
        deepspeech=deepspeech.Sink(speech=ds),
        httpd=httpd.Sink(control=http)
    )


def main():
    run(
        Component(call=deepspeech_server, input=DeepspeechSource),
        DeepspeechDrivers(
            deepspeech=deepspeech.make_driver(),
            httpd=httpd.make_driver(),
            argv=argv.make_driver(),
            stdout=stdout.make_driver(),
            file=file.make_driver()
        )
    )


if __name__ == '__main__':
    main()
