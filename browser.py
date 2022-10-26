import sys
import socket
import ssl
import tkinter

WIDTH, HEIGHT = 1600, 900
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


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


def lex(body):
    text = ""
    in_angle = False
    for char in body:
        if char == "<":
            in_angle = True
        elif char == ">":
            in_angle = False
        elif not in_angle:
            text += char
    return text


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for char in text:
        display_list.append((cursor_x, cursor_y, char))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


class Browser:
    def __init__(self):
        self.display_list = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)

    def load(self, url):
        headers, body = request(url)
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, char in self.display_list:
            if (y > self.scroll + HEIGHT) or (y + VSTEP < self.scroll): continue
            self.canvas.create_text(x, y - self.scroll, text=char)

    def scroll_down(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    Browser().load(sys.argv[1])
    tkinter.mainloop()
