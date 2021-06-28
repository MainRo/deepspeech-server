import json
from collections import namedtuple
from functools import partial
import asyncio
import rx
import rx.operators as ops
from rx.scheduler import ImmediateScheduler
from rx.scheduler.eventloop import AsyncIOScheduler

from cyclotron import Component
from cyclotron.router import make_error_router

from cyclotron.asyncio.runner import run
import cyclotron_aiohttp.httpd as httpd
import cyclotron_std.sys.argv as argv
import cyclotron_std.io.file as file
import cyclotron_std.argparse as argparse
import cyclotron_std.logging as logging

import deepspeech_server.deepspeech as deepspeech

from multidict import MultiDict

#from cyclotron.debug import trace_observable

DeepspeechSink = namedtuple('DeepspeechSink', [
     'logging', 'file', 'deepspeech', 'httpd'
])
DeepspeechSource = namedtuple('DeepspeechSource', [
    'deepspeech', 'httpd', 'file', 'argv'
])
DeepspeechDrivers = namedtuple('DeepspeechServerDrivers', [
    'logging', 'deepspeech', 'httpd', 'file', 'argv'
])


def parse_config(config_data):
    ''' takes a stream with the content of the configuration file as input
    and returns a (hot) stream of arguments .
    '''
    config = config_data.pipe(
        ops.filter(lambda i: i.id == "config"),
        ops.flat_map(lambda i: i.data),
        ops.map(lambda i: json.loads(
            i,
            object_hook=lambda d: namedtuple('x', d.keys())(*d.values()))),
        ops.share()
    )

    return config


def parse_arguments(argv):
    parser = argparse.ArgumentParser("deepspeech server")
    parser.add_argument(
        '--config', required=True,
        help="Path of the server configuration file")

    return argv.pipe(
        ops.skip(1),
        argparse.parse(parser),
    )


def deepspeech_server(aio_scheduler, sources):
    argv = sources.argv.argv
    stt = sources.httpd.route
    stt_response = sources.deepspeech.text
    ds_logs = sources.deepspeech.log

    http_ds_error, route_ds_error = make_error_router()

    args = parse_arguments(argv)

    read_request, read_response = args.pipe(
        ops.map(lambda i: file.Read(id='config', path=i.value)),
        file.read(sources.file.response),
    )
    read_request = read_request.pipe(
        ops.subscribe_on(aio_scheduler),
    )
    config = parse_config(read_response)

    logs_config = config.pipe(
        ops.flat_map(lambda i: rx.from_(i.log.level, scheduler=ImmediateScheduler())),
        ops.map(lambda i: logging.SetLevel(logger=i.logger, level=i.level)),
    )
    logs = rx.merge(logs_config, ds_logs)

    ds_stt = stt.pipe(
        ops.flat_map(lambda i: i.request),
        ops.map(lambda i: deepspeech.SpeechToText(data=i.data, context=i.context)),
    )

    # config is hot, the combine operator allows to keep its last value
    # until logging is initialized
    ds_arg = config.pipe(
        ops.map(lambda i: deepspeech.Initialize(
            model=i.deepspeech.model,
            scorer=deepspeech.Scorer(
                scorer=getattr(i.deepspeech, 'scorer', None),
                lm_alpha=getattr(i.deepspeech, 'lm_alpha', None),
                lm_beta=getattr(i.deepspeech, 'lm_beta', None),
            ),
            beam_width=getattr(i.deepspeech, 'beam_width', None),
        )),
    )
    ds = rx.merge(ds_stt, ds_arg)

    http_init = config.pipe(
        ops.flat_map(lambda i: rx.from_([
            httpd.Initialize(request_max_size=i.server.http.request_max_size),
            httpd.AddRoute(
                methods=['POST'],
                path='/stt',
                id='stt',
                headers=MultiDict([('Content-Type', 'text/plain')]),
            ),
            httpd.StartServer(
                host=i.server.http.host,
                port=i.server.http.port),
        ])),
    )

    http_response = stt_response.pipe(
        route_ds_error(
            error_map=lambda e: httpd.Response(
                data="Speech to text error".encode('utf-8'),
                context=e.args[0].context,
                status=500
        )),
        ops.map(lambda i: httpd.Response(
            data=i.text.encode('utf-8'),
            context=i.context,
        )),
    )

    http = rx.merge(http_init, http_response, http_ds_error)

    return DeepspeechSink(
        file=file.Sink(request=read_request),
        logging=logging.Sink(request=logs),
        deepspeech=deepspeech.Sink(speech=ds),
        httpd=httpd.Sink(control=http)
    )


def main():
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    aio_scheduler = AsyncIOScheduler(loop=loop)
    run(
        Component(
            call=partial(deepspeech_server, aio_scheduler),
            input=DeepspeechSource),
        DeepspeechDrivers(
            deepspeech=deepspeech.make_driver(),
            httpd=httpd.make_driver(),
            argv=argv.make_driver(),
            logging=logging.make_driver(),
            file=file.make_driver()
        ),
        loop=loop,
    )


if __name__ == '__main__':
    main()
