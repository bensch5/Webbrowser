import sys
import urllib.parse

from layout import *
from parser import *
from utils import *

DEFAULT_PAGE = "https://browser.engineering/"

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack()
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<BackSpace>", self.handle_backspace)
        self.window.bind("<Return>", self.handle_enter)
        self.tabs = []
        self.active_tab = None
        self.focus = None
        self.address_bar = ""

    def handle_down(self, e):
        self.tabs[self.active_tab].scroll_down()
        self.draw()

    def handle_up(self, e):
        self.tabs[self.active_tab].scroll_up()
        self.draw()

    def handle_click(self, e):
        if e.y < CHROME_PX:
            self.focus = None
            if 40 <= e.x < 40 + 80 * len(self.tabs) and 0 <= e.y < 40:
                self.active_tab = int((e.x - 40) / 80)
            elif 10 <= e.x < 35 and 40 <= e.y < 90:
                self.tabs[self.active_tab].go_back()
            elif 10 <= e.x < 30 and 10 <= e.y < 30:
                self.load(DEFAULT_PAGE)
            elif 50 <= e.x < WIDTH - 10 and 40 <= e.y < 90:
                self.focus = "address bar"
                self.address_bar = self.tabs[self.active_tab].url
        else:
            self.focus = "content"
            self.tabs[self.active_tab].click(e.x, e.y - CHROME_PX)
        self.draw()

    def handle_key(self, e):
        if len(e.char) == 0: return
        if not (0x20 <= ord(e.char) < 0x7f): return

        if self.focus == "address bar":
            self.address_bar += e.char
            self.draw()
        elif self.focus == "content":
            self.tabs[self.active_tab].keypress(e.char)
            self.draw()

    def handle_backspace(self, e):
        if self.focus == "address bar":
            self.address_bar = self.address_bar[:-1]
            self.draw()
        elif self.focus == "content":
            self.tabs[self.active_tab].backspace()
            self.draw()

    def handle_enter(self, e):
        if self.focus == "address bar":
            self.tabs[self.active_tab].load(self.address_bar)
            self.focus = None
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, WIDTH, CHROME_PX, fill="white", outline="black")
        self.tabs[self.active_tab].draw(self.canvas)
        tab_font = get_font(20, "normal", "roman")
        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = 40 + 80 * i, 120 + 80 * i
            self.canvas.create_line(x1, 0, x1, 40, fill="black")
            self.canvas.create_line(x2, 0, x2, 40, fill="black")
            self.canvas.create_text(x1 + 10, 10, anchor="nw", text=name, font=tab_font, fill="black")
            if i == self.active_tab:
                self.canvas.create_line(0, 40, x1, 40, fill="black")
                self.canvas.create_line(x2, 40, WIDTH, 40, fill="black")
        button_font = get_font(26, "normal", "roman")
        self.canvas.create_rectangle(10, 10, 30, 30,
                                     outline="black", width=1)
        self.canvas.create_text(11, 0, anchor="nw", text="+",
                                font=button_font, fill="black")
        self.canvas.create_rectangle(40, 50, WIDTH - 10, 90,
                                     outline="black", width=1)
        self.canvas.create_rectangle(10, 50, 35, 90,
                                     outline="black", width=1)
        self.canvas.create_polygon(
            15, 70, 30, 55, 30, 85, fill='black')
        if self.focus == "address bar":
            self.canvas.create_text(
                55, 55, anchor='nw', text=self.address_bar,
                font=button_font, fill="black")
            w = button_font.measure(self.address_bar)
            self.canvas.create_line(55 + w, 55, 55 + w, 85, fill="black")
        else:
            url = self.tabs[self.active_tab].url
            self.canvas.create_text(55, 55, anchor='nw', text=url,
                                    font=button_font, fill="black")

    def load(self, url):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()


class Tab:
    def __init__(self):
        self.rules = None
        self.scroll = 0
        self.url = None
        self.document = None
        self.display_list = []
        self.nodes = None
        with open("browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()
        self.history = []
        self.focus = None

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
            elif elt.tag == "input":
                self.focus = elt
                elt.attributes["value"] = ""
                return self.render()
            elif elt.tag == "button":
                while elt:
                    if elt.tag == "form" and "action" in elt.attributes:
                        return self.submit_form(elt)
                    elt = elt.parent
            elt = elt.parent

    def submit_form(self, elt):
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]

        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]
        url = resolve_url(elt.attributes["action"], self.url)
        self.load(url, body)

    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)

    def keypress(self, char):
        if self.focus:
            self.focus.attributes["value"] += char
            self.render()

    def backspace(self):
        if self.focus:
            self.focus.attributes["value"] = self.focus.attributes["value"][:-1]
            self.render()

    def load(self, url, body=None):
        self.history.append(url)
        self.url = url
        headers, body = request(url, body)
        self.nodes = HTMLParser(body).parse()
        self.rules = self.default_style_sheet.copy()
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
            self.rules.extend(CSSParser(body).parse())
        self.render()

    def render(self):
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        self.document.paint(self.display_list)

    def draw(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT - CHROME_PX:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - CHROME_PX, canvas)
        if self.focus:
            obj = [obj for obj in tree_to_list(self.document, [])
                   if obj.node == self.focus and \
                   isinstance(obj, InputLayout)][0]
            text = self.focus.attributes.get("value", "")
            x = obj.x + obj.font.measure(text)
            y = obj.y - self.scroll + CHROME_PX
            canvas.create_line(x, y, x, y + obj.height)

    def scroll_down(self):
        max_y = self.document.height - (HEIGHT - CHROME_PX)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)  # do not go past bottom of the page

    def scroll_up(self):
        if self.scroll >= SCROLL_STEP:  # do not go past top of the page
            self.scroll -= SCROLL_STEP


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = DEFAULT_PAGE
    Browser().load(url)
    tkinter.mainloop()


if __name__ == "__main__":
    main()
