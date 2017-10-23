import os
import json
from rx import Observable

from aiohttp import web, hdrs, WSMsgType

class AiohttpWsTransport():
    def __init__(self, handle):
        self.handle = handle

    def write(self, data):
        self.handle.send_str(data)

async def ws_handler(request):
    print('websocket request')
    ws = web.WebSocketResponse(protocols=('rxtender.1'))
    await ws.prepare(request)
    transport = AiohttpWsTransport(ws)
    router = SourceRouter(transport)
    def create_simple1_stream():
        print('create_simple1_stream')
        return None
    def delete_simple1_stream(stream):
        print('delete_simple1_stream')

    router.set_simple1_factory(create_simple1_stream, delete_simple1_stream)

    print('foo')
    await ws.send_str('foo')
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            print(msg.data)
            router.on_message(msg.data)
            #edleak_router(msg)
            '''
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
            '''
        elif msg.type == WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws


def setup_routes(app):
    project_root = os.path.dirname(edkit_server.__file__)

    app.router.add_get('/ws', ws_handler)
    app.router.add_static('/',
        path=project_root + '/static/edleak/',
        name='static')

    return


def http_driver():
    app = web.Application()

    def add_route(type, path):
        def on_add_route_subscribe(observer):
            def on_get_data(request):
                observer.on_next(request)
                return web.Response(text="Hello, world")

            app.router.add_get(path, on_get_data)

        route_observable = None
        if(type == "GET"):
            route_observable = Observable.create(lambda o: on_add_route_subscribe(o))
        return route_observable

    return {
        "add_route": add_route,
        "run": lambda: web.run_app(app, host='127.0.0.1', port=8000)
    }
