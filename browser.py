import sys
from layout import *
from parser import *
from utils import *


class Browser:
    def __init__(self):
        self.document = None
        self.display_list = []
        self.nodes = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<Button-1>", self.click)
        with open("browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.url = None

    def click(self, e):
        x, y = e.x, e.y
        y += self.scroll
        objs = [obj for obj in tree_to_list(self.document, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y <= y < obj.y + obj.height]
        if not objs:
            return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = resolve_url(elt.attributes["href"], self.url)
                return self.load(url)
            elt = elt.parent

    def load(self, url):
        self.url = url
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        rules = self.default_style_sheet.copy()
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                header, body = request(resolve_url(link, url))
            except:
                continue
            rules.extend(CSSParser(body).parse())
        style(self.nodes, sorted(rules, key=cascade_priority))  # file order as tiebreaker
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
