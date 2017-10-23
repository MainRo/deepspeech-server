

def console_driver(sink):
    sink.subscribe( lambda i: print('console: ' + i))
