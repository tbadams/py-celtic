import tkinter as tk
from tkinter import ttk
from enum import Enum
from typing import Optional
from collections import deque
import copy

# https://tkdocs.com/tutorial/canvas.html#tags

TAG_DOT = 'dot'
TAG_LINE = 'line'
TAG_KNOT = 'knot'
TAG_HELPER = 'helper'


class NodeType(Enum):
    PRIMARY = 1
    SECONDARY = 2
    LINE = 3


def get_node_type(col, row):
    if row % 2 == 0 and col % 2 == 0:
        return NodeType.PRIMARY
    elif row % 2 == 1 and col % 2 == 1:
        return NodeType.SECONDARY
    return NodeType.LINE


def get_lane_type(index: int):
    return NodeType.PRIMARY if index % 2 == 0 else NodeType.SECONDARY


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


class Block:

    def __init__(self, orientation: Orientation, index: int, start: int, end: int) -> None:
        self.orientation = orientation
        self.index = index
        self.start = start
        self.end = end

        #determine blocker type
        start_type = get_node_type(*self.start_coords())
        end_type = get_node_type(*self.end_coords())
        if start_type == end_type and start_type is not NodeType.LINE:
            self.block_type = start_type
        else:
            raise ValueError("illegal blocking line {} ({}) to {} ({})".format(str(self.start_coords()), str(start_type), str(self.end_coords()), str(end_type)))

    def start_coords(self):
        return (self.index, self.start) if self.orientation is Orientation.VERTICAL else (self.start, self.index)

    def end_coords(self):
        return (self.index, self.end) if self.orientation is Orientation.VERTICAL else (self.end, self.index)

    def invert(self, length:int, orientation:Orientation = Orientation.HORIZONTAL):
        # if orientation is Orientation.HORIZONTAL:
        #     if self.orientation is Orientation.VERTICAL:
        if orientation is not self.orientation:
            return Block(self.orientation, length - self.index, self.start, self.end)
        else:
            return Block(self.orientation, self.index, length- self.end, length - self.start)
        # else:
        #     raise NotImplementedError("you're killing me")

    def offset(self, offset:int, orientation:Orientation = Orientation.HORIZONTAL):
        index_offset = offset if orientation is not self.orientation else 0
        line_offset = offset if orientation is self.orientation else 0
        return Block(self.orientation, self.index + index_offset, self.start + line_offset, self.end + line_offset)

    def repeat(self, times:int, offset, orientation:Orientation = Orientation.HORIZONTAL):
        out = []
        for i in range(times):
            out.append(self.offset(i * offset, orientation))
        return out

    def fold(self):
        new_orientation = Orientation.HORIZONTAL if self.orientation is Orientation.VERTICAL else Orientation.VERTICAL
        return Block(new_orientation, self.index, self.start, self.end)


    def __str__(self) -> str:
        return "<{} -> {}>".format(str(self.start_coords()), str(self.end_coords()))


class VBlock(Block):
    def __init__(self, index: int, start: int, end: int) -> None:
        super().__init__(Orientation.VERTICAL, index, start, end)

class HBlock(Block):

    def __init__(self, index: int, start: int, end: int) -> None:
        super().__init__(Orientation.HORIZONTAL, index, start, end)

class LBlock(Block):
    def __init__(self, x1: int, y1: int, x2: int, y2) -> None:
        if x1 is x2:
            super().__init__(Orientation.VERTICAL, x1, y1, y2)
        elif y1 is y2:
            super().__init__(Orientation.HORIZONTAL, y1, x1, x2)
        else:
            raise ValueError("not a horizontal or vertical line: {}, {} -> {}, {}".format(x1, y1, x2, y2))



class PatternInterface:

    def get_length(self): raise NotImplementedError("please stop this")

    def add_block(self, line): raise NotImplementedError("cmon cmon")

    def append(self, pattern, orientation: Orientation = Orientation.HORIZONTAL):
        raise NotImplementedError("super super")

    def repeat(self, times:int, orientation = Orientation.HORIZONTAL):
        out = []
        for i in range(times):
            out.append(copy.deepcopy(self))
        return out
            # self.append(copy.deepcopy(self), orientation)

    def get_lines(self):
        raise NotImplementedError("no")

class Pattern(PatternInterface):

    length = 8
    height = 9

    def __init__(self, *lines, **kwargs) -> None:
        super().__init__()
        self.vertical_lines = {}
        self.horizontal_lines = {}
        self.__dict__.update(kwargs)
        for line in lines:
            self.add_block(line)

    def get_length(self): return self.length
    def get_height(self): return self.height

    def lines_for_orientation(self, orientation: Orientation):
        return self.horizontal_lines if orientation is Orientation.HORIZONTAL else self.vertical_lines

    def add(self, index: int, orientation: Orientation, line):
        # TODO merge lines somehow
        lines = self.lines_for_orientation(orientation)
        if index not in lines:
            lines[index] = []
        self.lines_for_orientation(orientation)[index].append(line)

    def add_block(self, line):
        self.add(line.index, line.orientation, (line.start, line.end))

    def append(self, pattern, orientation: Orientation = Orientation.HORIZONTAL):
        startx = 0
        starty = 0
        if (orientation is Orientation.HORIZONTAL):
            startx = self.length + 1
            self.length += pattern.length
        else:
            starty = self.height + 1
            self.height = pattern.height

        lines = self.get_lines()
        for line in lines:
            index_offset = startx if line.orientation is Orientation.VERTICAL else starty
            line_offset = starty if line.orientation is Orientation.VERTICAL else startx
            self.add_block(Block(line.orientation, line.index + index_offset, line.start + line_offset, line.end + line_offset))

        for row, lines in pattern.vertical_lines.items():
            for line in lines:
                self.vertical_lines[row + starty].append((line[0] + startx, line[1] + startx))
        for col, lines in pattern.horizontal_lines.items():
            for line in lines:
                self.horizontal_lines[col + startx].append((line[0] + starty, line[1] + starty))
        return self

    def get_lines(self):
        out = []
        for col, lines in self.vertical_lines.items():
            for line in lines:
                out.append(Block(Orientation.VERTICAL, col, line[0], line[1]))
        for row, lines in self.horizontal_lines.items():
            for line in lines:
                out.append(Block(Orientation.HORIZONTAL, row, line[0], line[1]))
        return out

    def invert(self, orientation:Orientation = Orientation.HORIZONTAL):
        return Pattern(*list(map(lambda line: line.invert(self.get_length(), orientation), self.get_lines())))

    def mirror(self, orientation:Orientation = Orientation.HORIZONTAL):
        if orientation is Orientation.HORIZONTAL:
            self.length = (self.length * 2) -1
            invert = self.length - 1
        else:
            self.height = (self.height * 2) -1
            invert = self.height -1
        lines = copy.deepcopy(self.get_lines())
        for line in lines:
            new_block = line.invert(invert, orientation)
            self.add_block(new_block)
        return self

    def fold(self):
        self.length = max(self.length, self.height)
        self.height = max(self.length, self.height)
        lines = copy.deepcopy(self.get_lines())
        for line in lines:
            self.add_block(line.fold())
        return self


    def __str__(self) -> str:
        return ','.join(list(map(str, self.get_lines())))


class HorizontalPatternGroup(PatternInterface):

    def __init__(self, *patterns) -> None:
        super().__init__()
        self.patterns = patterns


# class PatternGroup:
#     thresholds = {}
#
#     def __init__(self, *patterns) -> None:
#         super().__init__()
#         for pattern in patterns:
#





class KnotParams:

    def __init__(self, *patterns, **kwargs) -> None:
        super().__init__()

        self.__dict__.update(kwargs)
        if patterns:
            self.patterns = patterns
        else:
            self.patterns = [Pattern()]

    def get_height(self):
        return self.patterns[0].height

    def get_length(self):
        sum = 0
        for p in self.patterns:
            sum += p.length
        return sum

class ViewParams:
    unit_length = 24
    crossing_gap_length = 9
    dot_radius = 2
    primary_color = "blue"
    secondary_color = "violet"
    x_padding = 10
    y_padding = 10
    line_width = 12

    def __init__(self, line_color="black", **kwargs) -> None:
        super().__init__()
        self.line_color = line_color
        self.__dict__.update(kwargs)

    def get_color(self, node_type: NodeType):
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
        for col in range(self.kp.get_length()):
            if col not in self.vertical_blocks:
                self.vertical_blocks[col] = []
        self.vertical_blocks[0].append((0, self.kp.get_height() - 1))
        self.vertical_blocks[self.kp.get_length() - 1].append((0, self.kp.get_height() - 1))
        for row in range(self.kp.get_height()):
            if row not in self.horizontal_blocks:
                self.horizontal_blocks[row] = []
        self.horizontal_blocks[0].append((0, self.kp.get_length() - 1))
        self.horizontal_blocks[self.kp.get_height() - 1].append((0, self.kp.get_length() - 1))

        # input
        start_index = 0
        while start_index < self.kp.get_length():
            for pattern in self.kp.patterns:
                if pattern: # TODO fix
                    for col in pattern.vertical_lines:
                        self.vertical_blocks[col + start_index] = pattern.vertical_lines[col]
                    for row in pattern.horizontal_lines:
                        for blocker in pattern.horizontal_lines[row]:
                            self.horizontal_blocks[row].append((blocker[0] + start_index, blocker[1] + start_index))
                    start_index += pattern.length

        # setup crosses
        queue = deque()
        start = (1, 2)
        self.cross_dirs[start] = Diagonal.LEFTDOWN_RIGHTUP
        queue.append(start)
        while queue:
            next_node = queue.popleft()
            old_polarity = self.cross_dirs[next_node]
            new_polarity = Diagonal.LEFTUP_RIGHTDOWN if old_polarity == Diagonal.LEFTDOWN_RIGHTUP else Diagonal.LEFTDOWN_RIGHTUP
            neighbors = self.get_neighbors(*next_node)
            for neighbor in neighbors:
                if neighbor not in self.cross_dirs:
                    queue.append(neighbor)
                    self.cross_dirs[neighbor] = new_polarity  # if not self.is_blocking(*neighbor) else old_polarity

    def get_pixel(self, col, row):
        return self.vp.x_padding + (col * self.vp.unit_length), self.vp.y_padding + (row * self.vp.unit_length)

    def max_y(self):
        return self.vp.y_padding + (self.kp.get_height() - 1) * self.vp.unit_length

    def max_x(self):
        return self.vp.x_padding + (self.kp.get_length() - 1) * self.vp.unit_length

    def by_primary_index(self, col, row):
        pass

    def get_neighbors(self, col, row):
        out = [(col - 1, row - 1), (col + 1, row - 1), (col + 1, row + 1), (col - 1, row + 1)]
        return filter(
            lambda coord: 0 <= coord[0] < self.kp.get_length() and 0 <= coord[1] < self.kp.get_height(), out)

    def get_corners(self, x, y):
        half_unit = self.vp.unit_length / 2
        out: dict = {CornerDirection.LEFTUP: (x - half_unit, y - half_unit),
                     CornerDirection.RIGHTUP: (x + half_unit, y - half_unit),
                     CornerDirection.RIGHTDOWN: (x + half_unit, y + half_unit),
                     CornerDirection.LEFTDOWN: (x - half_unit, y + half_unit)}
        return dict(
            filter(lambda coord: 0 <= coord[1][0] < self.max_x() and 0 <= coord[1][1] < self.max_y(), out.items()))

    def is_blocking(self, col, row, orientation: Optional[Orientation] = None):
        if not orientation:
            return self.is_blocking(col, row, Orientation.HORIZONTAL) or self.is_blocking(col, row,
                                                                                          Orientation.VERTICAL)
        if orientation == Orientation.HORIZONTAL:
            blocks = self.horizontal_blocks[row]
            lane_index: int = col
        else:
            blocks = self.vertical_blocks[col]
            lane_index: int = row
        for block in blocks:
            block_start: int = block[0]
            block_end: int = block[1]
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

            self.create_line(crossing_adjusted_x, crossing_adjusted_y, *corner_coords, capstyle='butt')

    def create_line(self, x1, y1, x2, y2, node_type: NodeType = NodeType.LINE, state=None,
                    width: Optional[float] = None, color: str = None, capstyle:str = 'round'):
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
                                                     fill=color,
                                                     capstyle = capstyle))

    def draw_init(self):
        lines_drawn = []
        for row in range(0, self.kp.get_height()):
            for col in range(0, self.kp.get_length()):
                x, y = self.get_pixel(col, row)
                dr = self.vp.dot_radius
                nodetype = get_node_type(col, row)
                if nodetype is NodeType.PRIMARY:
                    color = self.vp.primary_color
                elif nodetype is NodeType.SECONDARY:
                    color = self.vp.secondary_color
                else:
                    color = None  # self.vp.line_color
                if color:
                    dot_id = self.canvas.create_oval(x - dr, y - dr, x + dr, y + dr, outline=color, fill=color,
                                                     state='hidden', tags=(TAG_DOT, TAG_HELPER))
                    self.dot_ids[x, y] = dot_id
                if nodetype is NodeType.LINE:
                    corners = self.get_corners(x, y)
                    if not self.is_blocking(col, row):
                        # normal two lines crossing
                        self.draw_lines_crossing(col, row)
                    else:
                        # lines bounce off a block
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
        for i, lines in self.horizontal_blocks.items():
            for line in lines:
                self.create_line(*self.get_pixel(line[0], i), *self.get_pixel(line[1], i),
                                 get_lane_type(i),
                                 width=self.vp.line_width / 2)
        for i, lines in self.vertical_blocks.items():
            for line in lines:
                self.create_line(*self.get_pixel(i, line[0]), *self.get_pixel(i, line[1]),
                                 get_lane_type(i),
                                 width=self.vp.line_width / 2)


def main(name):
    no_dots = {"primary_color": None, "secondary_color": None}
    classic_vp = ViewParams(crossing_gap_length = 6, line_width = 15)
    kpa = Pattern(vertical_lines={3: [(1, 3), (5, 7)]}, horizontal_lines={4: [(2, 4)]}, length=8)
    kpb = Pattern(vertical_lines={3: [(1, 3), (5, 7)]}, horizontal_lines={1: [(3, 11)], 7: [(3, 11)], 4: [(2, 4)]},
                  length=8)
    kpc = Pattern(vertical_lines={3: [(1, 3), (5, 7)], 6: [(2, 6)], 7: [(3, 5)], 8: [(2, 6)]},
                  horizontal_lines={4: [(2, 4)]}, length=8)
    skpa = Pattern(vertical_lines={1: [(1, 3)], 5: [(1, 3)]})
    skpb = Pattern(vertical_lines={1: [(1, 3)], 5: [(1, 3)], 9: [(1, 3)], 10: [(0, 2)], 12: [(2, 4)], 13: [(1, 3)]},
                   horizontal_lines={1: [(13, 15)], 2: [(6, 8)], 3: [(15, 17)]}, length=16)
    skpc = Pattern(vertical_lines={1: [(1, 3)], 5: [(1, 3)]},
                   horizontal_lines={1: [(5, 7)], 3: [(7, 9)]}, length=8)
    skpd = Pattern(vertical_lines={1: [(1, 3)]},
                   horizontal_lines={1: [(7, 9)], 3: [(7, 9)], 2: [(4, 6)]}, length=8)
    p1 = Pattern(Block(Orientation.VERTICAL, 1, 1, 3), length=2)
    p2 = Pattern(Block(Orientation.VERTICAL, 3, 1, 3), length=4)
    # p3 = Pattern(Block())
    p1a = Pattern(VBlock(1, 1, 3), VBlock(5, 1, 3), VBlock(9, 1, 3), VBlock(13, 1, 3), VBlock(17,1,3), VBlock(21, 1, 3), VBlock(6, 0,2), VBlock(8, 2, 4), HBlock(1, 13, 15), HBlock(3, 15,17), length=23, height = 5)
    p1b = Pattern(HBlock(1, 1, 3), HBlock(3, 3, 5), VBlock(1, 1, 3), VBlock(5, 1, 3), VBlock(9, 1, 3), VBlock(13, 1, 3),
                  VBlock(17, 1, 3), VBlock(21, 1, 3), VBlock(10, 0, 2), VBlock(12, 2, 4), HBlock(1, 19, 21), VBlock(3,3,5),
                  HBlock(3, 17, 19), HBlock(5,1,3), HBlock(4, 4,18), VBlock(4, 4, 18),
                  VBlock(2,20, 22), VBlock(4, 18, 20), HBlock(18, 2, 4), HBlock(20, 0, 2), length=23, height=23)
    p1c = Pattern(HBlock(1, 1, 3), HBlock(3, 3, 5), VBlock(1, 1, 3), VBlock(5, 1, 3), VBlock(9, 1, 3), VBlock(13, 1, 3),
                  VBlock(17, 1, 3), VBlock(21, 1, 3), HBlock(1, 15, 17), VBlock(3,3,5),
                  HBlock(3, 13, 15), HBlock(5,1,3), HBlock(4, 4,14), VBlock(4, 4, 18),
                  VBlock(2,20, 22), VBlock(4, 18, 20), HBlock(18, 2,
                                                              4), HBlock(20, 0, 2), length=19, height=41)
    p2a = Pattern(*VBlock(5, 1, 3).repeat(2, 4),  HBlock(1, 1, 3),  HBlock(3, 3, 5), HBlock(4,4,10), length=10, height=5).fold()
    p2b = Pattern(*p2a.get_lines(), VBlock(4, 10, 20), *HBlock(13, 1, 3).repeat(2, 4, orientation=Orientation.VERTICAL), HBlock(10,0,2), HBlock(12,2,4), length = p2a.length, height = (p2a.height * 2) -2)
    print(str(p2a))
    p2c = Pattern(*p2a.get_lines(), VBlock(4, 10, 20), *HBlock(13, 1, 3).repeat(2, 4, orientation=Orientation.VERTICAL),
                  HBlock(10, 0, 2), HBlock(12, 2, 4), length=8, height=8)
    printvp = ViewParams(crossing_gap_length = 6, line_width=15)
    final = p2b.mirror().mirror(Orientation.VERTICAL)
    finalb = p2c.mirror().mirror(Orientation.VERTICAL)
    delineator_start = 1
    delineator_interval = 4
    frame_width = 4
    block_length = 2
    corner_length = 8
    primary_corner_length = corner_length if corner_length % 2 == 0 else corner_length + 1
    quadrant_height = 18
    horizontal_alternators = [ HBlock(1, 1, 3),  HBlock(3, 3, 5)]
    delineators = [VBlock(i, 1, 3) for i in range(1, corner_length, 4)]
    inner_frame_corner =  HBlock(frame_width,frame_width,primary_corner_length)
    corner_lines = [*horizontal_alternators, *delineators, inner_frame_corner]
    inner_frame_side = VBlock(frame_width, primary_corner_length, quadrant_height)
    next_y = corner_length
    while (next_y - 1) % delineator_interval is not 0:
        next_y += 1
    side_deliniators = [HBlock(i, 1, 3) for i in range(next_y,quadrant_height, delineator_interval)]
    last_delineator_y = side_deliniators[-1].index
    vertical_alternators = [HBlock(last_delineator_y - 3,0,2), HBlock(last_delineator_y - 1,2,4)]
    quadrant = Pattern(*corner_lines, *list(map(lambda x: x.fold(), corner_lines)),
                       inner_frame_side, *side_deliniators,
                       *vertical_alternators, length=corner_length, height=quadrant_height)
    frame = quadrant.mirror().mirror(Orientation.VERTICAL)
    print("{} {}".format(frame.get_length()-1, frame.get_height()-1))
    kw = KnotWindow(vp=printvp, kp=KnotParams(frame))



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
