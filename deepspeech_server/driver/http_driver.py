import os
import json
import asyncio
from rx import Observable

from aiohttp import web


def http_driver(sink):
    app_args = {}
    run_args = {}
    app = None
    request_observer = None

    def add_route(type, path):
        async def on_post_data(request, path):
            ''' TODO: Handle errors. This could be done by making the request
            observable a stream of streams. Each request would be an Observable
            that carries zero or on item with the result payload, and either
            completes or fails. The stream completion would then complete the
            future.
            '''
            nonlocal request_observer
            data = await request.read()
            response_future = asyncio.Future()
            request_observer.on_next({
                "what": "data",
                "path": path,
                "data": data,
                "context": response_future
            })
            await response_future

            response = web.StreamResponse(status=200, reason=None)
            await response.prepare(request)
            await response.write(bytearray(response_future.result(), 'utf8'))
            return response

        if(type == "POST"):
            app.router.add_post(path, lambda r:on_post_data(r, path))

    def create_request_observable():
        def on_request_subscribe(observer):
            nonlocal request_observer
            request_observer = observer

        return Observable.create(on_request_subscribe)

    def on_sink_item(i):
        nonlocal app
        if i["what"] == "response":
            response_future = i["context"]
            response_future.set_result(i["data"])

        elif i["what"] == "srv_http_conf_request_max_size":
            app_args["client_max_size"] = i["value"]
        elif i["what"] == "srv_http_conf_port":
            run_args["port"] = i["value"]
        elif i["what"] == "srv_http_conf_host":
            run_args["host"] = i["value"]
        elif i["what"] == "conf_complete":
            app = web.Application(**app_args)

        elif i["what"] == "add_route":
            add_route(i["type"], i["path"])
        else:
            print("received unknown item: {}".format(i["what"]))

    sink.subscribe(on_sink_item)

    return {
        "request": create_request_observable,
        "run": lambda: web.run_app(app, **run_args)
    }
