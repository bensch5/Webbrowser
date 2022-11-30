import sys
from layout import Layout
from parser import HTMLParser
from utils import *


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
