from collections import namedtuple
import yaml
from typing import List, Optional
from xml.etree.ElementPath import ops
from pydantic import BaseModel

import rx.operators as ops


class Coqui(BaseModel):
    model: str
    scorer: Optional[str]
    beam_width: Optional[int]
    lm_alpha: Optional[float]
    lm_beta: Optional[float]


class HttpServer(BaseModel):
    host: str
    port: int
    request_max_size: int


class Server(BaseModel):
    http: HttpServer


class LogLevel(BaseModel):
    logger: str
    level: str

class Log(BaseModel):
    level: List[LogLevel]

class Config(BaseModel):
    coqui: Coqui
    server: Server
    log: Log


def parse_config(config_data):
    ''' takes a stream with the content of the configuration file as input
    and returns a (hot) stream of arguments .
    '''
    config = config_data.pipe(
        ops.filter(lambda i: i.id == "config"),
        ops.flat_map(lambda i: i.data),
        ops.map(lambda i: yaml.load(
            i,
            Loader=yaml.FullLoader    
        )),
        ops.map(lambda i: Config(**i)),
        ops.share(),
    )

    return config
