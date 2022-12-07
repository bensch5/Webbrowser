from utils import *
from parser import *


def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


class InlineLayout:
    def __init__(self, node, parent, previous):
        self.weight = "normal"
        self.style = "roman"
        self.family = "Times"
        self.size = 16
        self.height = None
        self.cursor_y = None
        self.cursor_x = None
        self.line = None
        self.display_list = None
        self.x = None
        self.y = None
        self.width = None
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.display_list = []
        self.line = []
        self.cursor_x = self.x
        self.cursor_y = self.y
        self.recurse(self.node)
        self.flush()
        self.height = self.cursor_y - self.y

    def recurse(self, node):
        if isinstance(node, Text):
            self.text(node)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)

    def text(self, node):
        color = node.style["color"]
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        font = get_font(self.family, size, weight, style)
        for word in node.text.split():  # remove white spaces
            w = font.measure(word)  # width
            if self.cursor_x + w > WIDTH - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font, color))
            self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return  # return if line is empty

        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font, color in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        self.line = []
        self.cursor_x = self.x
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list):
        bg_color = self.node.style.get("background-color", "transparent")
        if bg_color != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bg_color)
            display_list.append(rect)

        # if isinstance(self.node, Element) and self.node.tag == "pre":
        #     x2, y2 = self.x + self.width, self.y + self.height
        #     rect = DrawRect(self.x, self.y, x2, y2, "gray")
        #     display_list.append(rect)
        for x, y, word, font, color in self.display_list:
            display_list.append(DrawText(x, y, word, font, color))


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.height = None
        self.width = None
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        previous = None
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.node.children:
            if layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


class DocumentLayout:
    def __init__(self, node):
        self.x = None
        self.y = None
        self.height = None
        self.width = None
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_list):
        self.children[0].paint(display_list)


class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            fill=self.color,
            anchor='nw',
        )


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )
