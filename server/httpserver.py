import socket
import random
import urllib.parse

ENTRIES = [
    ("No names. We are nameless!", "cerealkiller"),
    ("HACK THE PLANET!!!", "crashoverride"),
]

LOGINS = {
    "crashoverride": "0cool",
    "cerealkiller": "emmanuel",
    "ada": "ada",
}

SESSIONS = {}

LIKES = 0


def show_comments(session):
    out = "<!doctype html>"

    for entry, who in ENTRIES:
        out += "<p>" + entry + "\n</p>"
        out += "<i>by " + who + "</i></p>"

    if "user" in session:
        out += "<h1>Hello, " + session["user"] + "</h1>"
        out += "<form action=add method=post>"
        out += "<p><input name=guest></p>"
        out += "<p><button>Sign the book!</button></p>"
        out += "</form>"
        out += "<label></label>"
        out += "<label></label>"
        out += "<script src='/comment.js'></script>"
        out += "<link href='/comment.css' rel='stylesheet'>"
    else:
        out += "<a href='/login'>Sign in to write in the guest book</a>"

    return out


def add_entry(session, params):
    if "user" not in session:
        return

    if 'guest' in params and len(params['guest']) <= 100:
        ENTRIES.append((params['guest'], session['user']))

    return show_comments(session)


def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out


def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params


def do_request(session, method, url, headers, body):
    print(method, url)

    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "GET" and url == "/login":
        return "200 OK", login_form(session)
    elif method == "GET" and url == "/comment.js":
        with open("comment.js") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/comment.css":
        with open("comment.css") as f:
            return "200 OK", f.read()
    elif method == "POST" and url == "/":
        params = form_decode(body)
        return do_login(session, params)
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        return "200 OK", add_entry(session, params)
    elif method == "POST" and url == "/likes":
        global LIKES
        LIKES = LIKES + 1
        return "200 OK", f"{LIKES}"
    elif method == "GET" and url == "/likes":
        return "200 OK", f"{LIKES}"
    else:
        return "404 Not Found", not_found(url, method)


def login_form(session):
    body = "<!doctype html>"
    body += "<form action='/' method='post'>"
    body += "<p>Username: <input name='username'></p>"
    body += "<p>Password: <input name='password' type='password'></p>"
    body += "<p><button>Log in</button></p>"
    body += "</form>"
    return body


def do_login(session, params):
    username = params.get("username")
    password = params.get("password")
    if username in LOGINS and LOGINS[username] == password:
        session["user"] = username
        return "200 OK", show_comments(session)
    else:
        out = "<!doctype html>"
        out += "<h1>Invalid password for {}</h1>".format(username)
        return "401 Unauthorized", out


def handle_connection(conx):
    req = conx.makefile("b")
    reqline = req.readline()
    try:
        reqline = reqline.decode('utf8')
    except UnicodeError:
        reqline = reqline.decode('ISO-8859-1')
    method, url, version = reqline.split(" ", 2)
    assert method in ["GET", "POST"]

    headers = {}
    for line in req:
        line = line.decode('utf8')
        if line == '\r\n':
            break

        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    if 'content-length' in headers:
        length = int(headers['content-length'])
        body = req.read(length).decode('utf8')
    else:
        body = None

    if 'cookie' in headers:
        token = headers['cookie'][len("token="):]
    else:
        token = str(random.random())[2:]

    session = SESSIONS.setdefault(token, {})
    status, body = do_request(session, method, url, headers, body)

    response = f"HTTP/1.0 {status}\r\n"
    response += "Content-Length: {}\r\n".format(len(body.encode('utf8')))

    if 'cookie' not in headers:
        template = "Set-Cookie: token={}\r\n"
        response += template.format(token)

    response += "\r\n" + body

    conx.send(response.encode('utf8'))
    conx.close()


def main():
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(('', 8000))
    s.listen()

    while True:
        conx, addr = s.accept()
        handle_connection(conx)


if __name__ == "__main__":
    main()
