import sys
from layout import *
from parser import HTMLParser
from utils import *


class Browser:
    def __init__(self):
        self.document = None
        self.display_list = []
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
        style(self.nodes)
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.document.paint(self.display_list)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def scroll_down(self, _e):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)  # do not go past bottom of the page
        self.draw()

    def scroll_up(self, _e):
        if self.scroll >= SCROLL_STEP:  # do not go past top of the page
            self.scroll -= SCROLL_STEP
        self.draw()


def main():
    Browser().load(sys.argv[1])
    tkinter.mainloop()


if __name__ == "__main__":
    main()
