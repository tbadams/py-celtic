import tkinter as tk
from tkinter import ttk
from enum import Enum
from typing import Optional


class NodeType(Enum):
    PRIMARY = 1
    SECONDARY = 2
    LINE = 3


class Orientation(Enum):
    HORIZONTAL = 1
    VERTICAL = 2


class Diagonal(Enum):
    LEFTDOWN_RIGHTUP = 1
    LEFTUP_RIGHTDOWN = 2


class CornerDirection(Enum):
    LEFTUP = 1
    RIGHTUP = 2
    RIGHTDOWN = 3
    LEFTDOWN = 4


class Pattern:
    vertical_lines = {}
    horizontal_lines = {2, (1, 2)}
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
    crossing_gap_length = 6
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
    horizontal_blocks: dict = {}
    vertical_blocks: dict = {}

    def __init__(self, kp: KnotParams = KnotParams(), vp: ViewParams = ViewParams()) -> None:
        super().__init__()
        self.kp = kp
        self.vp = vp

        # init borders
        for col in range(self.kp.cols):
            if col not in self.vertical_blocks:
                self.vertical_blocks[col] = []
        self.vertical_blocks[0].append((0, self.kp.rows - 1))
        self.vertical_blocks[self.kp.cols - 1].append((0, self.kp.rows - 1))
        for row in range(self.kp.rows):
            if row not in self.horizontal_blocks:
                self.horizontal_blocks[row] = []
        self.horizontal_blocks[0].append((0, self.kp.cols - 1))
        self.horizontal_blocks[self.kp.rows - 1].append((0, self.kp.cols - 1))

        window = tk.Tk()
        greeting = tk.Label(text="Knots")
        greeting.pack()
        canvas = tk.Canvas(window, bg="white", height=self.max_y() + self.vp.y_padding,
                           width=self.max_x() + self.vp.x_padding)
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

    def get_lane_type(self, index: int):
        return NodeType.PRIMARY if index % 2 == 0 else NodeType.SECONDARY

    def get_neighbors(self, col, row):
        out = [(col - 1, row - 1), (col + 1, row - 1), (col + 1, row + 1), (col - 1, row + 1)]
        return filter(
            lambda coord: 0 <= coord[0] < self.kp.cols - 1 and 0 <= coord[1] < self.kp.rows - 1, out)

    def get_corners(self, x, y):
        half_unit = self.vp.unit_length / 2
        out = {CornerDirection.LEFTUP: (x - half_unit, y - half_unit),
               CornerDirection.RIGHTUP: (x + half_unit, y - half_unit),
               CornerDirection.RIGHTDOWN: (x + half_unit, y + half_unit),
               CornerDirection.LEFTDOWN: (x - half_unit, y + half_unit)}
        return filter(
            lambda coord: 0 <= coord[1][0] < self.max_x() and 0 <= coord[1][1] < self.max_y(), out.items())

    def is_blocking(self, col, row, orientation:Optional[Orientation] = None):
        if not orientation:
            return self.is_blocking(col, row, Orientation.HORIZONTAL) or self.is_blocking(col, row, Orientation.VERTICAL)
        if orientation == Orientation.HORIZONTAL:
            blocks = self.horizontal_blocks[row]
            lane_index:int = col
        else:
            blocks = self.vertical_blocks[col]
            lane_index:int = row
        for block in blocks:
            block_start:int = block[0]
            block_end:int = block[1]
            if block_start <= lane_index <= block_end:
                return True
        return False

    def draw_coord_line(self, x1: int, y1: int, x2: int, y2: int):
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
                    color = None  # self.vp.line_color
                if color:
                    dot_id = self.canvas.create_oval(x - dr, y - dr, x + dr, y + dr, outline=color, fill=color)
                    self.dot_ids[x, y] = dot_id
                if nodetype is NodeType.LINE:
                    for corner in self.get_corners(x, y):
                        corner_type = corner[0]
                        corner_coords = corner[1]
                        crossing_adjusted_x = x
                        crossing_adjusted_y = y
                        cross_direction = Diagonal.LEFTDOWN_RIGHTUP  # TODO something else
                        if not self.is_blocking(col, row):
                            if (cross_direction == Diagonal.LEFTDOWN_RIGHTUP
                                and corner_type == CornerDirection.LEFTUP) or \
                                    (cross_direction == Diagonal.LEFTUP_RIGHTDOWN
                                     and corner_type == CornerDirection.LEFTDOWN):
                                crossing_adjusted_x = x - self.vp.crossing_gap_length
                            elif (cross_direction == Diagonal.LEFTDOWN_RIGHTUP
                                  and corner_type == CornerDirection.RIGHTDOWN) or (
                                    cross_direction == Diagonal.LEFTUP_RIGHTDOWN
                                    and corner_type == CornerDirection.RIGHTUP):
                                crossing_adjusted_x = x + self.vp.crossing_gap_length
                            if (cross_direction == Diagonal.LEFTDOWN_RIGHTUP
                                and corner_type == CornerDirection.LEFTUP) or \
                                    (cross_direction == Diagonal.LEFTUP_RIGHTDOWN
                                     and corner_type == CornerDirection.RIGHTUP):
                                crossing_adjusted_y = y - self.vp.crossing_gap_length
                            elif (cross_direction == Diagonal.LEFTDOWN_RIGHTUP
                                  and corner_type == CornerDirection.RIGHTDOWN) or (
                                    cross_direction == Diagonal.LEFTUP_RIGHTDOWN
                                    and corner_type == CornerDirection.LEFTDOWN):
                                crossing_adjusted_y = y + self.vp.crossing_gap_length

                        self.line_ids.append(self.canvas.create_line(crossing_adjusted_x, crossing_adjusted_y, *corner_coords,
                                                                     width=self.vp.line_width,
                                                                     fill=self.vp.line_color))

        # draw pattern
        dis_length = 0
        # while True:
        #     pass


def main(name):
    no_dots = {"primary_color":None, "secondary_color":None}
    kw = KnotWindow(vp=ViewParams(**no_dots))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
