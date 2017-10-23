from aiohttp import web
from rx import Observable
from rx.subjects import Subject

from collections import OrderedDict

from driver.http_driver import http_driver
from driver.console_driver import console_driver

def main(sources):
    '''
    async def handle(request):
        name = request.match_info.get('name', "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    app = web.Application()
    setup_routes(app)
# app.router.add_get('/', handle)
# app.router.add_get('/{name}', handle)

    web.run_app(app, host='127.0.0.1', port=8000)
    '''
    console = sources["HTTP"]["add_route"]("GET", "/stt")
    return OrderedDict([
        ("CONSOLE", console)
    ])


if __name__ == '__main__':

#   http_proxy = Subject()
    console_proxy = Subject()

    sources = OrderedDict([
        ("HTTP", http_driver()),
        ("CONSOLE", console_driver(console_proxy))        
    ])


    sinks = main(sources)

    sinks["CONSOLE"].subscribe()
    sources["HTTP"]["run"]()
    print("bar")
