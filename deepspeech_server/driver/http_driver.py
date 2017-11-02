import os
import json
from rx import Observable

from aiohttp import web


def http_driver(sink):
    app = web.Application()

    def add_route(type, path):
        def on_get_route_subscribe(observer):
            def on_get_data(request):
                observer.on_next(request)
                return web.Response(text="Hello, world")

            app.router.add_get(path, on_get_data)

        def on_post_route_subscribe(observer):
            async def on_post_data(request, path):
                data = await request.read()
                response = web.StreamResponse(status=200, reason=None)
                await response.prepare(request)
                observer.on_next({ "what": "data", "path": path, "data": data, "context": (request, response)})
                return response

            app.router.add_post(path, lambda r:on_post_data(r, path))

        route_observable = None
        if(type == "GET"):
            route_observable = Observable.create(on_get_route_subscribe)
        elif(type == "POST"):
            route_observable = Observable.create(on_post_route_subscribe)

        return route_observable

    def on_sink_item(i):
        (request, response) = i["context"]
        response.write(bytearray(i["data"], 'utf8'))

    sink.subscribe(on_sink_item)

    return {
        "add_route": add_route,
        "run": lambda: web.run_app(app, host='127.0.0.1', port=8000)
    }
