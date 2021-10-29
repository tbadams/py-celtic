import tkinter as tk
from tkinter import ttk
from enum import Enum

class NodeType(Enum):
    PRIMARY = 1
    SECONDARY = 2
    LINE = 3

class Direction(Enum):
    HORIZONTAL = 1
    VERTICAL = 2

class Pattern:
    vertical_lines = {}
    horizontal_lines = {2, (1,2)}
    length = 4

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)

class KnotParams:
    rows = 9
    cols = 33
    pattern = Pattern()

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)


class ViewParams:
    unit_length = 24
    dot_radius = 2
    primary_color = "blue"
    secondary_color = "violet"
    line_color = "lightgreen"
    x_padding = 10
    y_padding = 10
    line_width = 4

    def __init__(self, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)


class KnotWindow:
    dot_ids = {}
    line_ids = []
    horizontal_lines:dict={}
    vertical_lines:dict={}

    def __init__(self, kp: KnotParams = KnotParams(), vp: ViewParams = ViewParams()) -> None:
        super().__init__()
        self.kp = kp
        self.vp = vp

        # init borders
        for col in range(self.kp.cols):
            if col not in self.vertical_lines:
                self.vertical_lines[col] = []
        self.vertical_lines[0].append((0, self.kp.rows - 1))
        self.vertical_lines[self.kp.cols -1].append((0, self.kp.rows - 1))
        for row in range(self.kp.rows):
            if row not in self.horizontal_lines:
                self.horizontal_lines[row] = []
        self.horizontal_lines[0].append((0, self.kp.cols - 1))
        self.horizontal_lines[self.kp.rows -1].append((0, self.kp.cols - 1))

        window = tk.Tk()
        greeting = tk.Label(text="Knots")
        greeting.pack()
        canvas = tk.Canvas(window, bg="white", height=self.max_y()+self.vp.y_padding, width=self.max_x()+self.vp.x_padding)
        self.canvas = canvas
        canvas.pack()
        self.draw_init()

        window.mainloop()

    def get_pixel(self, col, row):
        return self.vp.x_padding + (col * self.vp.unit_length), self.vp.y_padding + (row * self.vp.unit_length)


    def max_y(self):
        return self.vp.y_padding + (self.kp.rows - 1) * self.vp.unit_length

    def max_x(self):
        return self.vp.x_padding + (self.kp.cols - 1) * self.vp.unit_length

    def by_primary_index(self, col, row):
        pass

    def get_node_type(self, col, row):
        if row % 2 == 0 and col % 2 == 0:
            return NodeType.PRIMARY
        elif row % 2 == 1 and col % 2 == 1:
            return NodeType.SECONDARY
        return NodeType.LINE


    def get_neighbors(self, col, row):
        out = [(col - 1, row-1), (col+1, row - 1), (col + 1, row+1), (col-1, row + 1)]
        return filter(
            lambda coord: 0 <= coord[0] < self.kp.cols -1 and 0 <= coord[1] < self.kp.rows -1, out)

    def get_corners(self, x, y):
        half_unit = self.vp.unit_length / 2
        out = [(x-half_unit, y-half_unit), (x+half_unit, y-half_unit), (x-half_unit,y+half_unit), (x+half_unit, y+half_unit)]
        return filter(
            lambda coord: 0 <= coord[0] < self.max_x() and 0 <= coord[1] < self.max_y(), out)


    def draw_coord_line(self, x1:int, y1:int, x2:int, y2:int):
        pass

    def draw_init(self):
        lines_drawn = []
        for row in range(0, self.kp.rows):
            for col in range(0, self.kp.cols):
                x, y = self.get_pixel(col, row)
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
                else:

                    for corner in self.get_corners(x,y):                   # if neighbor not in lines_drawn:
                            # print("{} {} {}".format(x, y, neighbor))
                        # self.line_ids.append(self.canvas.create_line(x, y, *self.get_pixel(*neighbor), width=self.vp.line_width, fill=self.vp.line_color))
                        self.line_ids.append(self.canvas.create_line(x, y, *corner,
                                                                     width=self.vp.line_width,
                                                                    fill=self.vp.line_color))

        # draw pattern
        dis_length = 0
        # while True:
        #     pass


def main(name):
    kw = KnotWindow(vp=ViewParams())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
