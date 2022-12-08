import sys
from layout import *
from parser import *
from utils import *


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack()
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        self.tabs = []
        self.active_tab = None

    def handle_down(self, e):
        self.tabs[self.active_tab].scroll_down()
        self.draw()

    def handle_up(self, e):
        self.tabs[self.active_tab].scroll_up()
        self.draw()

    def handle_click(self, e):
        self.tabs[self.active_tab].click(e.x, e.y)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.tabs[self.active_tab].draw(self.canvas)

    def load(self, url):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()


class Tab:
    def __init__(self):
        self.scroll = 0
        self.url = None
        self.document = None
        self.display_list = []
        self.nodes = None
        with open("browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()

    def click(self, x, y):
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

    def draw(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, canvas)

    def scroll_down(self):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)  # do not go past bottom of the page

    def scroll_up(self):
        if self.scroll >= SCROLL_STEP:  # do not go past top of the page
            self.scroll -= SCROLL_STEP


def main():
    Browser().load(sys.argv[1])
    tkinter.mainloop()


if __name__ == "__main__":
    main()
