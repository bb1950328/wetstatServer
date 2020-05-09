import datetime
import json
import os
import sys
from typing import Dict
from typing import List
from urllib import parse

di = os.path.abspath(os.path.dirname(__file__))
di2 = os.path.join(di, "venv", "lib")
di2 = os.path.join(di2, os.listdir(di2)[0], "site-packages")  # result of listdir is for example "python3.8"
if di not in sys.path:
    sys.path.append(di)
if di2 not in sys.path:
    sys.path.append(di2)
# print(sys.path, file=sys.stderr)

from wetstat.common import logger
from wetstat.model.db import db_model
from wetstat.sensors import sensor_master

ENVIRON_EXAMPLE = \
    {
        'CONTEXT_DOCUMENT_ROOT': '/home/pi/wetstatServer/http_root',
        'CONTEXT_PREFIX': '',
        'DOCUMENT_ROOT': '/home/pi/wetstatServer/http_root',
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate',
        'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
        'HTTP_CONNECTION': 'keep-alive',
        'HTTP_HOST': '192.168.178.27',
        'HTTP_UPGRADE_INSECURE_REQUESTS': '1',
        'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                           'rv:75.0) Gecko/20100101 Firefox/75.0',
        'PATH_INFO': '',
        'QUERY_STRING': '',
        'REMOTE_ADDR': '192.168.178.28',
        'REMOTE_PORT': '54192',
        'REQUEST_METHOD': 'GET',
        'REQUEST_SCHEME': 'http',
        'REQUEST_URI': '/api',
        'SCRIPT_FILENAME': '/home/pi/wetstatServer/wsgi_v2.py',
        'SCRIPT_NAME': '/api',
        'SERVER_ADDR': '192.168.178.27',
        'SERVER_ADMIN': 'webmaster@localhost',
        'SERVER_NAME': '192.168.178.27',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'SERVER_SIGNATURE': '<address>Apache/2.4.25 (Raspbian) '
                            'Server at 192.168.178.27 Port '
                            '80</address>\n',
        'SERVER_SOFTWARE': 'Apache/2.4.25 (Raspbian)',
        'apache.version': (2, 4, 25),
        'mod_wsgi.application_group': '',
        'mod_wsgi.callable_object': 'application',
        'mod_wsgi.daemon_connects': '1',
        'mod_wsgi.daemon_restarts': '0',
        'mod_wsgi.daemon_start': '1588786597264004',
        'mod_wsgi.enable_sendfile': '0',
        'mod_wsgi.handler_script': '',
        'mod_wsgi.ignore_activity': '0',
        'mod_wsgi.listener_host': '',
        'mod_wsgi.listener_port': '80',
        'mod_wsgi.path_info': '',
        'mod_wsgi.process_group': 'wetstatServer2',
        'mod_wsgi.queue_start': '1588786597259919',
        'mod_wsgi.request_handler': 'wsgi-script',
        'mod_wsgi.request_id': 'meXANNa7SbY',
        'mod_wsgi.request_start': '1588786597258649',
        'mod_wsgi.script_name': '/api',
        'mod_wsgi.script_reloading': '1',
        'mod_wsgi.script_start': '1588786597421057',
        'mod_wsgi.thread_id': 1,
        'mod_wsgi.thread_requests': 0,
        'mod_wsgi.total_requests': 0,
        'mod_wsgi.version': (4, 6, 4),
        'wsgi.errors': "<_io.TextIOWrapper name='<wsgi.errors>' encoding='utf-8'>",
        'wsgi.file_wrapper': "<class 'mod_wsgi.FileWrapper'>",
        'wsgi.input': "<mod_wsgi.Input object at 0xb6805ec0>",
        'wsgi.input_terminated': True,
        'wsgi.multiprocess': False,
        'wsgi.multithread': True,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'http',
        'wsgi.version': (1, 0)},


def to_bytes_csv(rows: List[List[object]]) -> bytes:
    return "\n".join(";".join(map(str, row)) for row in rows).encode()


def get_sensors(params: dict):
    data = []
    for sens in sensor_master.USED_SENSORS:
        data.append({
            "name": sens.get_long_name(),
            "short_name": sens.get_short_name(),
            "color": sens.get_display_color(),
            "unit": sens.get_unit(),
        })
    return json.dumps(data).encode(), "text/json"


def get_current_values(params: dict):
    values = sensor_master.get_current_values()
    if not values:
        values = db_model.find_nearest_record(datetime.datetime.now())
    heads = list(values.keys())
    row1 = []
    for sn in heads:
        val = values[sn]
        if isinstance(val, float):
            val = round(val, 2) if val < 1000 else int(round(val, 0))
        row1.append(str(val))
    return to_bytes_csv([heads, row1]), "text/csv"


def get_values(params: dict):
    return b"", "text/csv"


URI_FUNC_MAP = {
    "/api/sensors": get_sensors,
    "/api/current_values": get_current_values,
    "/api/values": get_values,
}


def application(environ: Dict[str, object], start_response: callable) -> list:
    content_type = "text/plain"
    try:
        full_uri = environ["REQUEST_URI"]
        params = {}
        if "?" in full_uri:
            uri, param_str = full_uri.split("?")
            for pair in param_str.split("&"):
                key, value = pair.split("=")
                params[key] = parse.unquote(value)
        else:
            uri = full_uri
        if uri in URI_FUNC_MAP.keys():
            status = "200 OK"
            result = URI_FUNC_MAP[uri](params)
            if isinstance(result, tuple) and len(result) == 2:
                output, content_type = result
            else:
                output = result
        else:
            status = "404 Not Found"
            output = b"The requestet URL " + uri.encode() + b" was not found."
    except Exception as e:
        logger.log.exception("Exception in wsgi_v2")
        status = "500 Server Error"
        output = str(e).encode()

    response_headers = [("Content-type", content_type),
                        ("Content-length", str(len(output)))]
    start_response(status, response_headers)
    return [output]
