import sys
import socket
import ssl
import tkinter
import tkinter.font
from layout import *


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


WIDTH, HEIGHT = 1600, 900
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
FONTS = {}


def get_font(family, size, weight, slant):
    key = (family, size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]


class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []  # text object will never have children
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + self.tag + ">"


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        for char in self.body:
            if char == "<":
                in_tag = True
                if text: self.add_text(text)  # if text -> don't add empty strings
                text = ""
            elif char == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += char
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attr_pair in parts[1:]:
            if "=" in attr_pair:
                key, value = attr_pair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]  # exclude quotation marks
                attributes[key.lower()] = value
            else:
                attributes[attr_pair.lower()] = ""
        return tag, attributes

    def add_text(self, text):
        if text.isspace(): return  # throw away empty text blocks
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def implicit_tags(self, tag):
        while True:  # more than one tag could have been omitted -> loop
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()


class Browser:
    def __init__(self):
        self.display_list = None
        self.nodes = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)

    def load(self, url):
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if (y > self.scroll + HEIGHT) or (y + VSTEP < self.scroll): continue
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor='nw')

    def scroll_down(self, _e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, _e):
        self.scroll -= SCROLL_STEP
        self.draw()


def main():
    Browser().load(sys.argv[1])
    tkinter.mainloop()


if __name__ == "__main__":
    main()
