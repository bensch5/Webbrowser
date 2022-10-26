import sys
import socket
import ssl


def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], "Unknown scheme {}".format(scheme)

    host, path = url.split("/", 1)
    path = "/" + path

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)
    elif scheme == "http":
        port = 80
    else:
        port = 443

    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") +
           "Host: {}\r\n\r\n".format(host).encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    status_line = response.readline()
    version, status, explanation = status_line.split(" ", 2)
    assert status == "200"  # , "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    s.close()

    return headers, body


def show(body):
    start_index = body.index("<body>")  # skip over html header tags
    in_angle = False
    for char in body[start_index:]:
        if char == "<":
            in_angle = True
        elif char == ">":
            in_angle = False
        elif not in_angle:
            print(char, end="")


def load(url):
    headers, body = request(url)
    show(body)


if __name__ == "__main__":
    load(sys.argv[1])

