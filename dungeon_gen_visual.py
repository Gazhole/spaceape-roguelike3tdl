import numpy as np
import random

# Set up predictable random number for testing.
PRNG = random.Random()
PRNG.seed(483957234345346347)


# Class to contain map array and drawing functions.
class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.ones([self.height, self.width], dtype=int)  # np arrays take x,y coordinates in reverse order.
        self.rooms = []  # to store room / rect objects.

    def display_in_console(self):
        # iterate through map coordinates and draw corresponding tile type from np array
        for y in range(self.height):
            for x in range(self.width):
                # 1 = blocked, 0 = open
                if self.grid[y, x] == 1:  # np arrays take x,y coordinates in reverse order.
                    char = "#"
                else:
                    char = "."
                print(char, end=' ')
            print('')


# basic rectangle object.
class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.x2 = x + w
        self.y1 = y
        self.y2 = y + h

    def carve(self, game_map):
        # iterate through rect coordinates and set tiles in map to open.
        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):
                Rect.carve_function(game_map, x, y)

    @staticmethod
    def carve_function(game_map, x, y):
        game_map.grid[y, x] = 0


def make_map(game_map, num_rooms, min_size, max_size, map_border, intersect_chance):
    # set variables for rooms to create, and sensible boundaries so rooms stay within map constraints.
    rooms_left = num_rooms
    first_room = True
    boundary_x = (map_border, game_map.width - map_border)
    boundary_y = (map_border, game_map.height - map_border)

    while rooms_left:
        new_room = create_room(boundary_x, boundary_y, min_size, max_size)

        if PRNG.randint(1, 100) > intersect_chance:
            if rooms_collide(game_map, new_room):
                continue

        try:
            new_room.carve(game_map)
        except IndexError:
            continue
        else:
            game_map.rooms.append(new_room)
            rooms_left -= 1

            if first_room:
                first_room = False
            else:
                previous_room = game_map.rooms[-2]
                create_corridoor(game_map, new_room, previous_room)


def create_room(boundary_x, boundary_y, min_size, max_size):
    while True:
        room_x, room_y = PRNG.randint(boundary_x[0], boundary_x[1]), PRNG.randint(boundary_y[0], boundary_y[1])

        max_width = (boundary_x[1]) - room_x
        max_height = (boundary_y[1]) - room_y

        if max_width > max_size:
            max_width = max_size
        elif max_width < min_size:
            continue

        if max_height > max_size:
            max_height = max_size
        elif max_height < min_size:
            continue

        room_w, room_h = PRNG.randint(min_size, max_width), PRNG.randint(min_size, max_height)

        room = Rect(room_x, room_y, room_w, room_h)
        break

    return room


def rooms_collide(game_map, new_room):
    for room in game_map.rooms:
        if room.x1 < new_room.x1 < room.x2 or room.x1 < new_room.x2 < room.x2 or room.y1 < new_room.y1 < room.y2 or room.y1 < new_room.y2 < room.y2:
            return True
    else:
        return False


def find_room_center(room):
    centre_x = int((room.x1 + room.x2) / 2)
    centre_y = int((room.y1 + room.y2) / 2)

    return centre_x, centre_y


def create_corridoor(game_map, new_room, previous_room):
    px, py = find_room_center(previous_room)
    nx, ny = find_room_center(new_room)
    breadth = PRNG.randint(1, 3)

    if PRNG.randint(0, 1) == 0:
        create_h_tunnel(game_map, px, nx, py, breadth)
        create_v_tunnel(game_map, py, ny, nx, breadth)
    else:
        create_v_tunnel(game_map, py, ny, px, breadth)
        create_h_tunnel(game_map, px, nx, ny, breadth)


def create_h_tunnel(game_map, x1, x2, y, h):
    for y in range(y, y + h):
        for x in range(min(x1, x2), max(x1, x2) + h):
            game_map.grid[y, x] = 0


def create_v_tunnel(game_map, y1, y2, x, w):
    for x in range(x, x + w):
        for y in range(min(y1, y2), max(y1, y2) + w):
            game_map.grid[y, x] = 0


map1 = Map(100, 100)
make_map(map1, num_rooms=15, min_size=5, max_size=25, map_border=2, intersect_chance=0)
map1.display_in_console()
