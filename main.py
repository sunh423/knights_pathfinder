import time
import pygame
import math
from queue import PriorityQueue

WIDTH_X = 800
LENGTH_Y = 800
pygame.init()
WIN = pygame.display.set_mode((WIDTH_X, LENGTH_Y))
FONT = pygame.font.SysFont("Calibiri", 23)
pygame.display.set_caption("Knight Pathfinding")

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
LIGHT_GREY = (64, 64, 64)
TURQUOISE = (64, 244, 208)


class Text_Window:
    def __init__(self, text, x=0, y=0, width=350, height=50, command=None):
        self.text = text
        self.command = command

        self.image_normal = pygame.Surface((width, height))
        self.image_normal.fill(LIGHT_GREY)

        self.image = self.image_normal
        self.rect = self.image.get_rect()

        text_image = FONT.render(text, True, WHITE)
        text_rect = text_image.get_rect(center=self.rect.center)

        self.image.blit(text_image, text_rect)

        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                if self.command:
                    self.command()


class Node:
    possible_status = ['fresh', 'path', 'open',
                       'closed', 'barrier', 'start', 'end']
    status_color = {'fresh': WHITE, 'open': GREEN, 'closed': RED,
                    'barrier': BLACK, 'start': ORANGE, 'end': PURPLE, 'path': YELLOW}

    def __init__(self, row, col, width_x, length_y, total_rows, total_columns, status="fresh"):
        self.row = row
        self.col = col
        self.x = row * length_y
        self.y = col * width_x
        self._status = status
        self.neighbors = []
        self.width = width_x
        self.length = length_y
        self.total_rows = total_rows
        self.total_columns = total_columns

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, update):
        if update in possible_status:
            self._status = update
        else:
            raise ValueError("That is not a valid status update")

    @status.getter
    def status(self):
        return Node.status_color[self._status]

    def get_pos(self):
        return self.row, self.col

    def is_closed(self):
        return self._status == "closed"

    def is_open(self):
        return self._status == "open"

    def is_barrier(self):
        return self._status == "barrier"

    def is_start(self):
        return self._status == "start"

    def is_end(self):
        return self._status == "end"

    def reset(self):
        self._status = "fresh"

    def make_closed(self):
        self._status = "closed"

    def make_open(self):
        self._status = "open"

    def make_barrier(self):
        self._status = "barrier"

    def make_start(self):
        self._status = "start"

    def make_end(self):
        self._status = "end"

    def make_path(self):
        self._status = "path"

    def draw(self, win):
        pygame.draw.rect(win, self.status,
                         (self.x, self.y, self.width, self.length))

    def update_neighbors(self, grid):
        self.neighbors = []
        try:
            if not grid[self.row - 1][self.col - 2].is_barrier():
                self.neighbors.append(
                    grid[self.row - 1][self.col - 2])  # top N1
        except IndexError:
            pass
        try:
            if not grid[self.row - 2][self.col - 1].is_barrier():
                self.neighbors.append(
                    grid[self.row - 2][self.col - 1])  # top N2
        except IndexError:
            pass
        try:
            if not grid[self.row - 2][self.col + 1].is_barrier():
                self.neighbors.append(
                    grid[self.row - 2][self.col + 1])  # top N3
        except IndexError:
            pass
        try:
            if not grid[self.row - 1][self.col + 2].is_barrier():
                self.neighbors.append(
                    grid[self.row - 1][self.col + 2])  # top N4
        except IndexError:
            pass
        try:
            if not grid[self.row + 1][self.col - 2].is_barrier():
                self.neighbors.append(
                    grid[self.row + 1][self.col - 2])  # bottom N1
        except IndexError:
            pass
        try:
            if not grid[self.row + 2][self.col - 1].is_barrier():
                self.neighbors.append(
                    grid[self.row + 2][self.col - 1])  # bottom N1
        except IndexError:
            pass
        try:
            if not grid[self.row + 2][self.col + 1].is_barrier():
                self.neighbors.append(
                    grid[self.row + 2][self.col + 1])  # bottom N1
        except IndexError:
            pass
        try:
            if not grid[self.row + 1][self.col + 2].is_barrier():
                self.neighbors.append(
                    grid[self.row + 1][self.col + 2])  # bottom N1
        except IndexError:
            pass

    def __lt__(self, other):
        return False


def h(p1, p2):  # Heuristic function to determine distance between two nodes
    x1, y1 = p1
    x2, y2 = p2
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)


def reconstruct_path(previous_node, current, draw):
    steps = 0
    while current in previous_node:
        current = previous_node[current]
        current.make_path()
        draw()
        steps += 1
    return steps


# our A* pathfinding algorithm we are going to use
def algorithm(draw, grid, start, end, win):
    t1 = time.time()
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    previous_node = {}
    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0
    f_score = {node: float("inf") for row in grid for node in row}
    f_score[start] = h(start.get_pos(), end.get_pos())

    open_set_hash = {start}

    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = open_set.get()[2]
        open_set_hash.remove(current)

        if current == end:
            print(time.time() - t1)
            steps = reconstruct_path(previous_node, end, draw)
            end.make_end()
            start.make_start()
            return True, steps  # make path, draw all the previous nodes

        for neighbor in current.neighbors:  # if one of the neighboring nodes is shortest, go with that one
            temp_g_score = g_score[current] + 2

            if temp_g_score < g_score[neighbor]:
                previous_node[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + \
                    h(neighbor.get_pos(), end.get_pos())
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    neighbor.make_open()
        draw()

        if current != start:
            current.make_closed()

    return False, 0


# Creates nodes and a nested list for data array
def make_grid(rows, columns, width, length):
    grid = []
    w_gap = width // rows
    l_gap = length // columns
    for i in range(rows):
        grid.append([])
        for j in range(columns):
            node = Node(i, j, w_gap, l_gap, rows, columns)
            grid[i].append(node)
    return grid


# Draws all the gridlines to separate the nodes.
def draw_gridlines(win, rows, columns, width, length):
    w_gap = width // rows
    l_gap = length // columns
    for i in range(rows):
        # pygame.draw.line(SURAFE, COLOR, start x/y, end x/y)
        pygame.draw.line(win, GREY, (0, i * w_gap), (width, i * w_gap))
    for j in range(columns):
        pygame.draw.line(win, GREY, (j * l_gap, 0), (j * l_gap, length))


def draw(win, grid, rows, columns, width, length):
    win.fill(WHITE)

    for row in grid:
        for node in row:
            node.draw(win)
    draw_gridlines(win, rows, columns, width, length)
    pygame.display.update()


def get_clicked_pos(pos, rows, columns, width, length):
    w_gap = width // rows
    l_gap = width // columns
    y, x = pos

    row = y // l_gap
    col = x // w_gap

    return row, col


def main(win, width, length):
    ROWS = 50
    COLS = 50
    grid = make_grid(ROWS, COLS, width, length)

    wall_toggle = False

    start = None
    end = None

    run = True

    result = None
    steps = None

    while run:
        if result != None:
            if result:
                popup = Text_Window(
                    f"Shortest path was found! Number of moves: {steps}")
                popup.draw(win)
                pygame.display.update()
            else:
                popup = Text_Window(f"No path was found! :(")
                popup.draw(win)
                pygame.display.update()
        else:
            draw(win, grid, ROWS, COLS, width, length)
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False

            # mouse gives a list of booleans for different mouse keys. 0 refer to left click
            if pygame.mouse.get_pressed()[0] and result == None:
                pos = pygame.mouse.get_pos()
                row, col = get_clicked_pos(pos, ROWS, COLS, width, length)
                node = grid[row][col]
                if not start and node != end:
                    start = node
                    start.make_start()
                if not end and node != start:
                    end = node
                    end.make_end()
                elif node != end and node != start:
                    node.make_barrier()

            # mouse gives a list of booleans for different mouse keys. 2 refer to right click
            if pygame.mouse.get_pressed()[2] and result == None:
                pos = pygame.mouse.get_pos()
                row, col = get_clicked_pos(pos, ROWS, COLS, width, length)
                node = grid[row][col]
                node.reset()
                if node == start:
                    start = None
                elif node == end:
                    end = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and start and end and result == None:
                    for row in grid:
                        for node in row:
                            node.update_neighbors(grid)

                    result, steps = algorithm(lambda: draw(
                        win, grid, ROWS, COLS, width, length), grid, start, end, win)
                    draw(win, grid, ROWS, COLS, width, length)

                if event.key == pygame.K_c:
                    start = None
                    end = None
                    grid = make_grid(ROWS, COLS, width, length)
                    wall_toggle = False
                    result = None

                if event.key == pygame.K_t and result == None:
                    if not wall_toggle:
                        for row in grid:
                            for node in row:
                                if node.row == 0 or node.row == 1 or node.col == 0 or node.col == 1 or node.col == COLS - 1 or node.col == COLS - 2 or node.row == ROWS - 1 or node.row == ROWS - 2:
                                    node.make_barrier()
                        wall_toggle = True
                    elif wall_toggle:
                        for row in grid:
                            for node in row:
                                if node.row == 0 or node.row == 1 or node.col == 0 or node.col == 1 or node.col == COLS - 1 or node.col == COLS - 2 or node.row == ROWS - 1 or node.row == ROWS - 2:
                                    node.reset()
                        wall_toggle = False
    pygame.quit()


main(WIN, WIDTH_X, LENGTH_Y)
