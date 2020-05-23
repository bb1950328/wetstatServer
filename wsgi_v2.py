import datetime
import json
import os
import sys
import time
import traceback
from typing import Dict
from typing import List
from urllib import parse

di = os.path.abspath(os.path.dirname(__file__))
di2 = os.path.join(di, "venv", "lib")
di2 = os.path.join(di2, os.listdir(di2)[0], "site-packages")  # result of listdir is for example ["python3.8"]
if di not in sys.path:
    sys.path.append(di)
if di2 not in sys.path:
    sys.path.append(di2)
# print(sys.path, file=sys.stderr)

from wetstat.model.db import connection_pool
from wetstat.common import logger
from wetstat.model.db import db_model
from wetstat.sensors import sensor_master

wsgi_environ = {}


def to_bytes_csv(rows: List[List[object]]) -> bytes:
    return "\n".join([row_to_csv(row) for row in rows]).encode()


def row_to_csv(row: list) -> str:
    # sorry for bad readability, but it's faster ;-)
    res = ["" if val is None
           else str(round(val, 2 if val < 1000 else 0) if isinstance(val, float)
                    else (int(val.timestamp()) if isinstance(val, datetime.datetime)
                          else val))
           for val in row]
    return ";".join(res)


def get_sensors(params: dict):
    data = []
    for sens in sensor_master.USED_SENSORS:
        data.append({
            "name": sens.get_long_name(),
            "short_name": sens.get_short_name(),
            "color": sens.get_display_color(),
            "unit": sens.get_unit(),
        })
    return json.dumps(data).encode(), "application/json"


def get_current_values(params: dict):
    now = datetime.datetime.now()
    values = sensor_master.get_current_values()
    if not values:
        values = db_model.find_nearest_record(now)
    sum_sensors = [sens.get_short_name() for sens in sensor_master.SUM_SENSORS]
    if sum_sensors:
        values.update(db_model.get_value_sums(sum_sensors, end=now, duration=datetime.timedelta(days=1)))
    heads = list(values.keys())
    row1 = [values[sn] for sn in heads]
    return to_bytes_csv([heads, row1]), "text/csv"


def get_values(params: dict):
    start = time.perf_counter()

    params.setdefault("to", int(time.time()))
    params.setdefault("from", int(time.time() - 60 * 60 * 24 * 365))
    from_ = datetime.datetime.fromtimestamp(int(params["from"]))
    to = datetime.datetime.fromtimestamp(int(params["to"]))
    data = db_model.load_data_for_date_range(from_, to)
    rows = list(data.array)
    result = to_bytes_csv([data.columns, *rows]), "text/csv"

    stop = time.perf_counter()
    used = (stop - start)
    print("Used", used, "s for ", len(rows), "rows, that's", used / len(rows), "s/row", file=sys.stderr)
    return result


def next_value(params: dict):
    params.setdefault("to", int(time.time()))
    params.setdefault("sum_span", 60 * 60 * 24)
    to = datetime.datetime.fromtimestamp(int(params["to"]))
    sum_span = datetime.timedelta(seconds=params["sum_span"])
    values = db_model.find_nearest_record(to)
    sum_sensors = [sens.get_short_name() for sens in sensor_master.SUM_SENSORS]
    if sum_sensors:
        values.update(db_model.get_value_sums(sum_sensors, end=to, duration=sum_span))
    heads = list(values.keys())
    row1 = [values[sn] for sn in heads]
    return to_bytes_csv([heads, row1]), "text/csv"


def to_serializable_dict(inp: dict) -> dict:
    res = {}
    for key, value in inp.items():
        try:
            json.dumps(value)
        except TypeError:
            res[key] = str(value)
        else:
            res[key] = value
    return res


def system_info(params: dict):
    return json.dumps({
        "pid": os.getpid(),
        "executable": sys.executable,
        "used_db_connections": connection_pool.get_used_count(),
        "open_db_connections": connection_pool.get_open_count(),
        "wsgi_environ": to_serializable_dict(wsgi_environ),
    }).encode(), "application/json"


URI_FUNC_MAP = {
    "/api/sensors": get_sensors,
    "/api/current_values": get_current_values,
    "/api/values": get_values,
    "/api/next_value": next_value,
    "/api/system_info": system_info,
}


def application(environ: Dict[str, object], start_response: callable) -> list:
    content_type = "text/plain"
    global wsgi_environ
    wsgi_environ = environ
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
        output = traceback.format_exc().encode()

    response_headers = [("Content-type", content_type),
                        ("Content-length", str(len(output)))]
    start_response(status, response_headers)
    return [output]
