import tkinter as tk
from tkinter import ttk
from enum import Enum

class NodeType(Enum):
    PRIMARY = 1
    SECONDARY = 2
    LINE = 3


class KnotParams:
    rows = 4
    cols = 32

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)


class ViewParams:
    height = 720
    width = 720
    unit_length = 24
    dot_radius = 2
    primary_color = "blue"
    secondary_color = "violet"
    line_color = "lightgreen"
    x_padding = 10
    y_padding = 10

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)


class KnotWindow:
    dot_ids = {}
    line_ids = {}

    def __init__(self, kp: KnotParams = KnotParams(), vp: ViewParams = ViewParams()) -> None:
        super().__init__()
        self.kp = kp
        self.vp = vp
        window = tk.Tk()
        greeting = tk.Label(text="Knots")
        greeting.pack()
        canvas = tk.Canvas(window, bg="white", height=vp.height, width=vp.width)
        self.canvas = canvas
        canvas.pack()
        self.draw_dots()

        window.mainloop()

    def get_pixel(self, col, row):
        return self.vp.x_padding + (col * self.vp.unit_length), self.vp.y_padding + (row * self.vp.unit_length)

    def by_primary_index(self, col, row):
        pass

    def get_node_type(self, col, row):
        if row % 2 == 0 and col % 2 == 0:
            return NodeType.PRIMARY
        elif row % 2 == 1 and col % 2 == 1:
            return NodeType.SECONDARY
        return NodeType.LINE


    def get_neighbors(self, col, row):
        out = [(col - 1, row), (col, row - 1), (col + 1, row), (col, row + 1)]
        out = filter(
            lambda coord: coord[0] >= 0 and coord[0] < self.kp.cols and coord[1] >= 0 and coord[1] < self.kp.rows)

    def draw_dots(self):
        for row in range(0, self.kp.rows * 2 - 1):
            for col in range(0, self.kp.cols * 2 - 1):
                x, y = self.get_pixel(col * 2, row * 2)
                dr = self.vp.dot_radius
                nodetype = self.get_node_type(col, row)
                if nodetype is NodeType.PRIMARY:
                    color = self.vp.primary_color
                elif nodetype is NodeType.SECONDARY:
                    color = self.vp.secondary_color
                else:
                    color = None # self.vp.line_color
                if color:
                    dot_id = self.canvas.create_oval(x - dr, y - dr, x + dr, y + dr, outline=color, fill=color)
                    self.dot_ids[x, y] = dot_id


def main(name):
    kw = KnotWindow()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
