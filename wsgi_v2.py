import pprint

def application(environ, start_response):
    status = "200 OK"
    try:
    	output = b"Hello from Python ;-)\n"
    	output += pprint.pformat(dict(globals(), **locals()), indent=4).encode("utf-8")
    except Exception as e:
        output = str(e).encode()

    response_headers = [("Content-type", "text/plain"),
                        ("Content-length", str(len(output)))]
    start_response(status, response_headers)
    return [output]
