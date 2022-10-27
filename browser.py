import sys
import socket
import ssl
import tkinter
import tkinter.font

WIDTH, HEIGHT = 1600, 900
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
FONTS = {}


def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https", "file"], "Unknown scheme {}".format(scheme)

    headers = {}

    if scheme == "file":
        path = url[1:]
        file = open(path)
        body = file.read()
    else:
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
    out = []
    text = ""
    in_tag = False
    for char in body:
        if char == "<":
            in_tag = True
            if text: out.append(Text(text))  # if text -> don't add empty strings
            text = ""
        elif char == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += char
    if not in_tag and text:
        out.append(Text(text))
    return out


class Text:
    def __init__(self, text):
        self.text = text


class Tag:
    def __init__(self, tag):
        self.tag = tag


def get_font(family, size, weight, slant):
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.family = "Times"
        self.size = 16
        for token in tokens:
            self.process_token(token)
        self.flush()

    def process_token(self, token):
        if isinstance(token, Text):
            self.process_text(token.text)
        else:
            self.process_tag(token.tag)

    def process_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "/i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "/b":
            self.weight = "normal"
        elif tag == "small":
            self.size -= 2
        elif tag == "/small":
            self.size += 2
        elif tag == "big":
            self.size += 4
        elif tag == "/big":
            self.size -= 4
        elif tag == "br":
            self.flush()
        elif tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def process_text(self, text):
        font = get_font(self.family, self.size, self.weight, self.style)
        for word in text.split():  # remove white spaces
            w = font.measure(word)  # width
            if self.cursor_x + w > WIDTH - HSTEP: self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return  # return if line is empty

        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.line = []
        self.cursor_x = HSTEP
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent


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
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, char, font in self.display_list:
            if (y > self.scroll + HEIGHT) or (y + VSTEP < self.scroll): continue
            self.canvas.create_text(x, y - self.scroll, text=char, font=font, anchor='nw')

    def scroll_down(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    Browser().load(sys.argv[1])
    tkinter.mainloop()
