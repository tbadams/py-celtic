import tkinter as tk
from tkinter import ttk
from enum import Enum
from typing import Optional
from collections import deque


# https://tkdocs.com/tutorial/canvas.html#tags

TAG_DOT = 'dot'
TAG_LINE = 'line'
TAG_KNOT = 'knot'
TAG_HELPER = 'helper'

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
    horizontal_lines = {}
    length = 8
    height = 9

    def __init__(self, *lines, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)

    def lines_for_orientation(self, orientation:Orientation):
        return self.horizontal_lines if orientation is Orientation.HORIZONTAL else self.vertical_lines

    def add(self, index:int, orientation:Orientation, line):
        # TODO merge lines somehow
        self.lines_for_orientation(orientation)[index].append(line)

    def append(self, pattern, orientation:Orientation = Orientation.VERTICAL):
        startx = 0
        starty = 0
        if (orientation is Orientation.VERTICAL):
            startx = self.length + 1
            self.length += pattern.length
        else:
            starty = self.height + 1
            self.height = pattern.height

        for row, lines in pattern.horizontal_lines.items:
            for line in lines:
                self.horizontal_lines[row + starty].append((line[0] + startx, line[1] + startx))
        for col, lines in pattern.horizontal_lines.items:
            for line in lines:
                self.horizontal_lines[col + startx].append((line[0] + starty, line[1] + starty))



class KnotParams:
    rows = 9
    cols = 33
    patterns = [Pattern()]

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

    def get_color(self, node_type:NodeType):
        if node_type == NodeType.PRIMARY:
            return self.primary_color
        if node_type == NodeType.SECONDARY:
            return self.secondary_color
        if node_type == NodeType.LINE:
            return self.line_color
        raise ValueError('unknown node type {}'.format(node_type))


class KnotWindow:
    dot_ids = {}
    line_ids = []
    horizontal_blocks: dict = {}
    vertical_blocks: dict = {}
    cross_dirs = {}
    helpers_hidden = True

    def __init__(self, kp: KnotParams = KnotParams(), vp: ViewParams = ViewParams()) -> None:
        super().__init__()
        self.kp = kp
        self.vp = vp

        self.setup_blocks()

        window = tk.Tk()
        greeting = tk.Label(text="Knots")
        greeting.pack()
        canvas = tk.Canvas(window, bg="white", height=self.max_y() + self.vp.y_padding,
                           width=self.max_x() + self.vp.x_padding)
        self.canvas = canvas
        canvas.pack()
        self.draw_init()
        hide_helpers_button = tk.Button(window, text="Toggle (H)elpers", command=self.toggle_helpers)
        hide_helpers_button.pack()

        # Hotkeys
        window.bind('h', lambda e: self.toggle_helpers())
        window.bind('H', lambda e: self.toggle_helpers())

        window.mainloop()

    def setup_blocks(self):
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

        # input
        start_index = 0
        while start_index < self.kp.cols:
            for pattern in self.kp.patterns:
                for col in self.kp.pattern.vertical_lines:
                    self.vertical_blocks[col+start_index] = self.kp.pattern.vertical_lines[col]
                for row in self.kp.pattern.horizontal_lines:
                    for blocker in self.kp.pattern.horizontal_lines[row]:
                        self.horizontal_blocks[row].append((blocker[0]+start_index, blocker[1]+start_index))
                start_index += pattern.length

        # setup crosses
        queue = deque()
        start = (1, 2)
        self.cross_dirs[start] = Diagonal.LEFTDOWN_RIGHTUP
        queue.append(start)
        while queue:
            next_node = queue.popleft()
            old_polarity = self.cross_dirs[next_node]
            new_polarity = Diagonal.LEFTUP_RIGHTDOWN if old_polarity==Diagonal.LEFTDOWN_RIGHTUP else Diagonal.LEFTDOWN_RIGHTUP
            neighbors = self.get_neighbors(*next_node)
            for neighbor in neighbors:
                if neighbor not in self.cross_dirs:
                    queue.append(neighbor)
                    self.cross_dirs[neighbor] = new_polarity #if not self.is_blocking(*neighbor) else old_polarity


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
            lambda coord: 0 <= coord[0] < self.kp.cols  and 0 <= coord[1] < self.kp.rows, out)

    def get_corners(self, x, y):
        half_unit = self.vp.unit_length / 2
        out:dict = {CornerDirection.LEFTUP: (x - half_unit, y - half_unit),
               CornerDirection.RIGHTUP: (x + half_unit, y - half_unit),
               CornerDirection.RIGHTDOWN: (x + half_unit, y + half_unit),
               CornerDirection.LEFTDOWN: (x - half_unit, y + half_unit)}
        return dict(filter(lambda coord: 0 <= coord[1][0] < self.max_x() and 0 <= coord[1][1] < self.max_y(), out.items()))

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

    def toggle_helpers(self):
        self.helpers_hidden = not self.helpers_hidden
        self.canvas.itemconfigure(TAG_HELPER, state='hidden' if self.helpers_hidden else 'normal')

    def draw_lines_crossing(self, col, row):
        x, y = self.get_pixel(col, row)
        corners = self.get_corners(x, y)
        for corner in corners.items():
            corner_type = corner[0]
            corner_coords = corner[1]
            crossing_adjusted_x = x
            crossing_adjusted_y = y
            cross_direction = self.cross_dirs[(col, row)]
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

            self.create_line(crossing_adjusted_x, crossing_adjusted_y, *corner_coords)

    def create_line(self, x1, y1, x2, y2, node_type:NodeType = NodeType.LINE, state=None, width:Optional[float] = None, color:str = None):
        if color is None:
            color = self.vp.get_color(node_type)
        if width is None:
            width = self.vp.line_width
        if state is None:
            state = 'normal' if node_type is NodeType.LINE else 'hidden'
        if node_type is NodeType.LINE:
            tags = (TAG_LINE, TAG_KNOT)
        else:
            tags = (TAG_LINE, TAG_HELPER)

        self.line_ids.append(self.canvas.create_line(x1, y1, x2, y2,
                                tags=tags,
                                state=state,
                                width=width,
                                fill=color))

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
                    dot_id = self.canvas.create_oval(x - dr, y - dr, x + dr, y + dr, outline=color, fill=color, state='hidden', tags=(TAG_DOT, TAG_HELPER ))
                    self.dot_ids[x, y] = dot_id
                if nodetype is NodeType.LINE:
                    corners = self.get_corners(x, y)
                    if not self.is_blocking(col, row):
                        # normal two lines crossing
                        self.draw_lines_crossing(col, row)
                    else:
                        #lines bounce off a block
                        if self.is_blocking(col, row, Orientation.VERTICAL):
                            if CornerDirection.LEFTUP in corners and CornerDirection.LEFTDOWN in corners:
                                    self.create_line(*corners[CornerDirection.LEFTUP], *corners[CornerDirection.LEFTDOWN])
                            if CornerDirection.RIGHTUP in corners and CornerDirection.RIGHTDOWN in corners:
                                    self.create_line(*corners[CornerDirection.RIGHTUP],
                                                            *corners[CornerDirection.RIGHTDOWN])
                        elif self.is_blocking(col, row, Orientation.HORIZONTAL):
                            if CornerDirection.LEFTUP in corners and CornerDirection.RIGHTUP in corners:
                                    self.create_line(*corners[CornerDirection.LEFTUP], *corners[CornerDirection.RIGHTUP])
                            if CornerDirection.LEFTDOWN in corners and CornerDirection.RIGHTDOWN in corners:
                                    self.create_line(*corners[CornerDirection.LEFTDOWN],
                                                            *corners[CornerDirection.RIGHTDOWN])
        # draw blocking line helpers
        for i,lines in self.horizontal_blocks.items():
            for line in lines:
                self.create_line(*self.get_pixel(line[0], i), *self.get_pixel(line[1], i),
                                                             self.get_lane_type(i),
                                                             width=self.vp.line_width/2)
        for i,lines in self.vertical_blocks.items():
            for line in lines:
                self.create_line(*self.get_pixel(i, line[0]), *self.get_pixel(i, line[1]),
                                                            self.get_lane_type(i),
                                                             width=self.vp.line_width/2)


def main(name):
    no_dots = {"primary_color":None, "secondary_color":None}
    kpa = Pattern(  vertical_lines = {3:[(1,3), (5,7)]}, horizontal_lines = {4:[(2, 4)]}, length = 8)
    kpb = Pattern(  vertical_lines = {3:[(1,3), (5,7)]}, horizontal_lines = {1:[(3,11)], 7:[(3,11)], 4:[(2, 4)]}, length = 8)
    kpc = Pattern(  vertical_lines = {3:[(1,3), (5,7)], 6:[(2,6)], 7:[(3,5)], 8:[(2,6)]}, horizontal_lines = {4:[(2, 4)]}, length = 8)
    skpa = Pattern(vertical_lines={1:[(1,3)], 5:[(1,3)]})
    skpb = Pattern(vertical_lines={1:[(1,3)], 5:[(1,3)], 9:[(1,3)], 10:[(0,2)],12:[(2,4)], 13:[(1,3)]}, horizontal_lines={1:[(13,15)], 2:[(6,8)], 3:[(15,17)]}, length=16)
    skpc = Pattern(vertical_lines={1: [(1, 3)], 5: [(1, 3)]},
                   horizontal_lines={1: [(5, 7)], 3: [(7,9)]}, length=8)
    skpd = Pattern(vertical_lines={1: [(1, 3)]},
                   horizontal_lines={1:[(7,9)], 3: [(7,9)], 2:[(4,6)]}, length=8)
    kw = KnotWindow(vp=ViewParams(), kp=KnotParams(rows=5, pattern=skpd))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
