from tdl.map import Map
import numpy as np
import random
from entity_classes import Monster, Pickup
from render_functions import get_render_char
from entity_classes import stats
import math
from entity_templates import monster_manual, item_manual


# TODO: Features to add
# Exploration loops (when linking rooms cross link automatically every few rooms)
# Fix weird door layouts in intersected rooms - ALMOST DONE!!! Just walls along a wall adjacent.
# Entry and Exit placeholders to check journey
# Stop monsters spawning in first room.
# Place secret doors.
# Place button doors.


# Set up predictable random number for testing.
PRNG = random.Random()
seed = random.randint(1, 1000000)

# # Testing levels
# seed = 888727
# seed = 513201
# seed = 130875
# seed = 524937

PRNG.seed(seed)
print(seed)


class GameMap(Map):
    """
    GameMap object which stores information about the game world the player has to navigate.
    Includes arrays to keep track of walls, doors, buttons, and the ground.
    Inherits from the TDL map class so incorporates the libtcod FOV function and parameters.

    ATTRIBUTES:
        - width / weight (int): the dimensions of the map in console tiles.
        - explored (numpy array - bool): tracks whether the tile has been seen by the player.
        - viable_coords (numpy array - bool): a representation of whether this tile is free for initial entity placement
        - is_door (numpy array - bool): refers to whether a given tile is a door, or a switch controlling a door.
        - door (list array - False or Object): a container for Door or Button objects, usually accessed via is_door
        - r, g, b represent the colour value of each tile.

    Contains two methods - one to set a particular tile as a door during map creation, and another to allow the player
    to open that door during gameplay (accessed via the engine / main game loop).

    INIT:
        - Calls the TDL map object and initialises arrays for FOV using the width and height parameters.
        - Creates basic numpy arrays with False as default value (explored, viable_coords, is_door)
        - Creates a nested list to store door objects (False by default) as numpy arrays cannot contain objects.
    """
    def __init__(self, map_width, map_height):
        super().__init__(map_width, map_height)
        self.width = map_width
        self.height = map_height
        self.rooms = []

        self.r = np.array([[250 for y in range(map_height)] for x in range(map_width)])
        self.g = np.array([[250 for y in range(map_height)] for x in range(map_width)])
        self.b = np.array([[250 for y in range(map_height)] for x in range(map_width)])

        self.explored = np.array([[False for y in range(map_height)] for x in range(map_width)])
        self.viable_coords = np.array([[False for y in range(map_height)] for x in range(map_width)])

        self.is_door = np.array([[False for y in range(map_height)] for x in range(map_width)])
        self.door = [[False for y in range(map_height)] for x in range(map_width)]

    # TODO: Doc
    def save_map_to_file(self, entities_list):
        filename = str(seed) + ".txt"
        with open(filename, "w") as file:
            for y in range(self.height):
                for x in range(self.width):
                    door = self.is_door[x, y]
                    wall = not self.walkable[x, y] and not self.transparent[x, y] and not door
                    ground = self.walkable[x, y] and self.transparent[x, y] and not door

                    for entity in entities_list:
                        if entity.x == x and entity.y == y:
                            door = False
                            wall = False
                            ground = False
                            monster = entity

                    if door:
                        print("+", end='', file=file)
                    elif wall:
                        print("#", end='', file=file)
                    elif ground:
                        print(".", end='', file=file)
                    else:
                        print(monster.char, end='', file=file)
                print("", file=file)

    # TODO: Doc
    def set_tile_colour(self, x, y, colour):
        r, g, b = colour

        self.r[x, y] = r
        self.g[x, y] = g
        self.b[x, y] = b

    def set_door(self, x, y, w=1, h=1, secret=False, button=False):
        """
        This method is typically called during map creation, for the purpose of creating a door in the game map.

        PARAMETERS:
            - x, y (int): the first tile position of the door in the game map.
            - w, h (int): the width and height of the door. Bear in mind that these are absolute, referring to x and y axes.
            - secret (bool): is this door is a normal door (the default, secret being False) or a secret door.
            - button (False or tuple(x, y, colour): is this door can be activated at it's own location, or done via a button.
              (if not a button door, set False (default), but if this is a button door a tuple (x, y) must be provided.

        DESCRIPTION:
              By default a door is a single tile with a width and height of 1, but multi-tile doors can be created.
              By specifying non-default dimensions, the x, y tile is the first tile in the door, and width/height are
              used as a range to iterate through for additional tiles.

              In effect, a multi-tile door is not one object but a grid of different instances of the same object class

              A normal door will have a visible console character drawn on screen, and can be activated by a player
              walking into the tile containing the door.

              A secret door will be drawn as if it were a wall and thus is not visible to the player.

              A button door can only be activated using it's linked button - walking into it will have no effect

              The combination of these features can create a normal door, a locked door, a secret "push-wall" or
              a hidden/surprise room.

        """

        '''
        Due to a quirk in the auto-tiling function, secret doors must be two tiles "thick" in order for the correct
        wall tile to be drawn. This is a slight bug produced by the way tile-types are detected using integer masking
        resulting in multiple tile-types producing an identical mask value, so w and h need to be set to at least 2
        if the door will be a secret door.
        '''

        if secret and w == 1 and h > 1:
            w = 2
        elif secret and h == 1 and w > 1:
            h = 2

        # Create a rect, adding width & height to x and y (the top left point) to calculate the bottom right point
        x1 = x
        y1 = y
        x2 = x + w
        y2 = y + h

        # Iterate through the x and y ranges for each tile in this theoretical rect to set each of the tiles as door
        for ycoord in range(y1, y2):
            for xcoord in range(x1, x2):
                '''
                Remove this tile from the viable coords list.
                Set as not transparent (blocks FOV).
                Make the tile not walkable (blocks movement).
                Mark as a door (is_door array) and create a Door object (in the door array).
                '''
                self.viable_coords[xcoord, ycoord] = False
                self.transparent[xcoord, ycoord] = False
                self.walkable[xcoord, ycoord] = False
                self.is_door[xcoord, ycoord] = True
                self.door[xcoord][ycoord] = Door(secret, button)
                self.set_tile_colour(xcoord, ycoord, (250, 250, 250))

                '''
                If the door is a secret door, we need to render "nothing" (i.e. the floor) when the door is open.
                When the door is closed, we need to render a wall as normal so we hijack the auto-tiling function
                from the rendering function set to do the same job.
                '''
                if secret:
                    self.door[xcoord][ycoord].open_char = 197
                    self.door[xcoord][ycoord].closed_char = get_render_char(self, x, y)

        if button:
            '''
            If this door is activated with a button, we need to repeat the above steps to create a "door" at the button
            location. First unpack the tuple (x, y) provided to the button parameter, repeat the normal steps to setting
            the tile as a door (but instead, use the Button object instead of Door, storing in door array.
            Finally, set some special console characters to be rendered for the button instead of it looking like a door
            '''
            button_x, button_y, colour = button
            self.viable_coords[button_x, button_y] = False
            self.transparent[button_x, button_y] = False
            self.walkable[button_x, button_y] = False
            self.is_door[button_x, button_y] = True

            for ycoord in range(y1, y2):
                for xcoord in range(x1, x2):
                    self.set_tile_colour(xcoord, ycoord, colour)

            self.door[button_x][button_y] = Button(button_x, button_y, x, y)
            self.door[button_x][button_y].open_char = "/"
            self.door[button_x][button_y].closed_char = "\\"
            self.set_tile_colour(button_x, button_y, colour)

    def open_door(self, x, y):
        """
        PARAMETERS:
            - x, y (int): the location on the map of the door to be opened.

        This function should be called from the main game loop in the engine, or triggered from a Button object.

        Taking an x and y coordinate of a Door or Button object, that door or button is set to open.
        By definition an open door is one which can be walked through by the player and allows light to pass.

        To account for multi-tile doors (i.e which are bigger than 1x1, the open_door method is run recursively in
        each cardinal direction if the adjacent tile in that direction is also a door.

        Because a multi-tile door is not one single object taking up more map, instead being a collection of single tile
        Door objects, this is required to set all connected Door objects which make up our door to open at the same time
        and triggered by any single tile which makes up that door on the map.
        """

        self.door[x][y].is_open = True
        self.transparent[x, y] = True
        self.walkable[x, y] = True
        set_tile_colour_light_to_dark(self, x, y)

        # The if statements check whether each adjacent tile (cardinal) is a door and not open.

        if self.is_door[x - 1, y] and not self.door[x - 1][y].is_open:
            self.open_door(x - 1, y)

        if self.is_door[x + 1, y] and not self.door[x + 1][y].is_open:
            self.open_door(x + 1, y)

        if self.is_door[x, y - 1] and not self.door[x][y - 1].is_open:
            self.open_door(x, y - 1)

        if self.is_door[x, y + 1] and not self.door[x][y + 1].is_open:
            self.open_door(x, y + 1)


class Door:
    """
    A simple class to represent a door on the map. Door objects are stored in an array in the game_map and are
    solely accessed through interactions with that array, and are created through the GameMap.set_door function.

    By default, the console characters open_char and closed_char are set to +/- but the set_door function will check
    against the "secret" attribute in order to change these characters to a dynamic one set by the auto-tiler based
    on the door's position on the map.

    Also, by default the attribute "is_open" is set to False.

    ATTRIBUTE:
        secret (bool): is this a secret door?
        button (bool): can this door only be activated via a button?
        is_open (bool): is the door open?
        open_char / closed_char (str / int): the console character to be rendered. Either a single character string, or
            a libtcod ASCII constant which is an integer.
    """
    def __init__(self, secret=False, button=False):
        self.is_open = False
        self.secret = secret
        self.button = button

        self.open_char = "-"
        self.closed_char = "+"


class Button(Door):
    """
    The Button is created when a remote-controlled door is created. Because the Button shares similar behaviours with
    the Door (the ability to be opened, involving a change of character, needs to be stored as part of the map rather
    than a true Entity), it made sense to sub-class from Door.

    ATTRIBUTES:
         x, y (int): the location of the button on the map.
         target_x, target_y (int): the location of the target door this button should open.

    Even though Button is a sub-class of Door, at the moment the "secret" and "button" attributes should be set to False
    to avoid an invisible button, or useless chains of buttons which do nothing. A line of invisible buttons could be
    a good candidate for a "trip wire" type mechanism to open secret chambers unexpectedly.
    """
    def __init__(self, button_x, button_y, target_x, target_y):
        super().__init__(secret=False, button=False)
        self.x = button_x
        self.y = button_y
        self.target_x = target_x
        self.target_y = target_y

    def open_door(self, game_map):
        """
        The open_door function borrows the name from the equivalent function from GameMap on purpose.
        When the button is triggered from a check in the main loop in the engine script, two instances of
        GameMap.open_door are triggered - one on the button itself (merely to change the look of the button) and one
        on the target of the button (the closed door).
        """
        game_map.open_door(self.x, self.y)
        game_map.open_door(self.target_x, self.target_y)


class Rect:
    """
    Basic class to calculate a simple rectangular shape.
    Takes the coordinates (x, y) of the top left corner point (x1, y1) and the width (w) / height (h) of the rectangle.
    Using this info the bottom right point is calculated (x2, y2).
    Contains a class method to "carve" the rectangle out of the map (i.e. set to transparent and walkable).
    The carve function will add all carved coordinates to the game map's viable coordinates.
    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.x2 = x + w
        self.y1 = y
        self.y2 = y + h

        self.inside = []

    def carve(self, game_map):
        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):
                carve_function(game_map, x, y)
                self.inside.append((x, y))


# TODO: doc all functions
class Room(Rect):
    def __init__(self, x, y, w=None, h=None, square=True):
        random_width, random_height = Room._set_size(square=square)

        if not w:
            if square and h:
                w = h
            else:
                w = random_width

        if not h:
            if square and w:
                h = w
            else:
                h = random_height

        super().__init__(x, y, w, h)

        self.walls = self._get_walls()
        self.center = self.get_center()

    # TODO: Doc
    def get_center(self):
        centre_x = int((self.x1 + self.x2) / 2)
        centre_y = int((self.y1 + self.y2) / 2)

        return centre_x, centre_y

    # TODO: Doc
    def _get_walls(self):
        walls = []
        walls.extend([(x, self.y1 - 1) for x in range(self.x1, self.x2)])
        walls.extend([(self.x2, y) for y in range(self.y1, self.y2)])
        walls.extend([(x, self.y2) for x in range(self.x1, self.x2)])
        walls.extend([(self.x1 - 1, y) for y in range(self.y1, self.y2)])
        return walls

    # TODO: Doc
    @staticmethod
    def _set_size(square=True):
        possible_sizes = [9, 11, 13, 15, 17]

        if square:
            w = PRNG.choice(possible_sizes)
            h = w

        else:
            w = PRNG.choice(possible_sizes)
            h = PRNG.choice(possible_sizes)

        return w, h


def get_viable_coordinates(game_map):
    """
    Takes the numpy array in game_map representing viable coordinates, and searches for all "True" value indices (x, y).
    Zips these together into individual cartesian coordinates (tuples) in a list.
    Returns this array for use in entity placement functions.
    """
    viable_x, viable_y = np.where(game_map.viable_coords)
    viable_coords = list(zip(viable_x, viable_y))

    return viable_coords


def place_entity(game_map, entity, entities_list, room=None):
    """
    Using a list of viable coordinates from the game map, selects one point at random, and updates the entity's location
    This point is then set to False in GameMap.viable and removed from the viable coords list.

    :param viable_coords: List of viable map coordinates as a tuple i.e. (x, y)
    :param game_map: The GameMap object
    :param entity: The entity to be placed
    """
    viable_coords = get_viable_coordinates(game_map)

    if room:
        while True:
            place = PRNG.choice(room.inside)
            if place in viable_coords:
                break
            else:
                continue
    else:
        place = PRNG.choice(viable_coords)

    place_x, place_y = place
    viable_coords.remove(place)

    entity.x, entity.y = place_x, place_y
    game_map.viable_coords[place_x, place_y] = False
    entities_list.append(entity)


def place_monsters(game_map, entities_list, max_number_of_entities, room=None):
    for i in range(PRNG.randint(0, max_number_of_entities)):
        monster_name, monster_char, monster_colour, monster_stats = PRNG.choice(monster_manual["level1"])
        monster = Monster(0, 0, monster_name, monster_char, monster_colour, monster_stats)
        place_entity(game_map, monster, entities_list, room=room)


def place_pickups(game_map, entities_list, max_number_of_entities, room=None):
    for i in range(PRNG.randint(0, max_number_of_entities)):
        item_name, item_char, item_colour, item_stats = PRNG.choice(item_manual["level1"])
        item = Pickup(0, 0, item_name, item_char, item_colour, item_stats)
        place_entity(game_map, item, entities_list, room=room)


# TODO: Doc
def dungeon_generator_complex(game_map, player, entities_list, max_monsters_per_room, max_items_per_room, num_rooms, cross_link_chance, intersect_chance, map_border=3):
    boundary_x = (map_border, game_map.width - map_border)
    boundary_y = (map_border, game_map.height - map_border)

    first_room = create_room(game_map, boundary_x, boundary_y, intersect_chance)
    player.x, player.y = first_room.center

    for i in range(num_rooms - 1):
        room = create_room(game_map, boundary_x, boundary_y, intersect_chance, square=False)
        place_monsters(game_map, entities_list, max_monsters_per_room, room=room)
        place_pickups(game_map, entities_list, max_items_per_room, room=room)

    rooms_to_link = list(game_map.rooms)

    current_room = first_room
    for i in range(num_rooms):
        new_room = get_closest_room(rooms_to_link, current_room)

        if not new_room:
            break
        else:
            create_corridor(game_map, current_room, new_room)
            current_room = new_room

    number_of_cross_links = int((len(game_map.rooms) * int(cross_link_chance / 10)) / 10)

    for i in range(number_of_cross_links):
        rooms_to_cross_link = list(game_map.rooms)

        previous_room = PRNG.choice(rooms_to_cross_link)
        rooms_to_cross_link.remove(previous_room)

        new_room = PRNG.choice(rooms_to_cross_link)
        create_corridor(game_map, previous_room, new_room)

    set_doors(game_map)
    remove_junk_doors(game_map, boundary_x, boundary_y)
    place_monsters(game_map, entities_list, max_number_of_entities=num_rooms)
    place_pickups(game_map, entities_list, max_number_of_entities=num_rooms)

    game_map.save_map_to_file(entities_list)


# TODO: Doc
def get_closest_room(rooms_to_link, current_room):
    proximity_map = dict()

    for room in rooms_to_link:
        if id(room) == id(current_room):
            continue
        else:
            x1, y1 = current_room.center
            x2, y2 = room.center
            distance = math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))
            proximity_map[distance] = room

    rooms_by_distance = sorted(proximity_map.keys())
    if not rooms_by_distance:
        return 0
    else:
        closest_room = rooms_by_distance[0]
        rooms_to_link.remove(current_room)

    return proximity_map[closest_room]


# TODO: doc
def set_doors(game_map):
    for room in game_map.rooms:
        for x, y in room.walls:
            if game_map.walkable[x, y]:
                game_map.set_door(x, y)


# TODO: Doc
def remove_junk_doors(game_map, boundary_x, boundary_y):
    change = False

    for y in range(boundary_y[0], boundary_y[1]):
        for x in range(boundary_x[0], boundary_x[1]):
            if game_map.is_door[x, y]:
                north_tile = (x, y - 1)
                east_tile = (x + 1, y)
                south_tile = (x, y + 1)
                west_tile = (x - 1, y)

                tiles = [north_tile, east_tile, south_tile, west_tile]

                tile_map = list()
                for tile in tiles:
                    tx, ty = tile
                    tile_type = get_tile_type(game_map, tx, ty)
                    tile_map.append(tile_type)

                blank = {"wall": False, "ground": True, "door": False}

                blank_score = 0
                for tile in tile_map:
                    if tile == blank:
                        blank_score += 1

                if blank_score > 2:
                    game_map.is_door[x, y] = False
                    game_map.door[x][y] = False
                    carve_function(game_map, x, y)
                    change = True

    if change:
        remove_junk_doors(game_map, boundary_x, boundary_y)


# TODO: Doc
def get_tile_type(game_map, x, y):
    wall = not game_map.transparent[x, y] and not game_map.walkable[x, y] and not game_map.is_door[x, y]
    ground = game_map.transparent[x, y] and game_map.walkable[x, y] and not game_map.is_door[x, y]
    door = game_map.is_door[x, y]

    return {"wall": wall, "ground": ground, "door": door}


# TODO: Doc
def create_corridor(game_map, previous_room, new_room):
    px, py = previous_room.center
    nx, ny = new_room.center

    previous_room_rows = set([y for y in range(previous_room.y1 + 1, previous_room.y2 - 1)])
    new_room_rows = set([y for y in range(new_room.y1 + 1, new_room.y2 - 1)])
    matching_rows = previous_room_rows.intersection(new_room_rows)

    previous_room_columns = set([x for x in range(previous_room.x1 + 1, previous_room.x2 - 1)])
    new_room_columns = set([x for x in range(new_room.x1 + 1, new_room.x2 - 1)])
    matching_columns = previous_room_columns.intersection(new_room_columns)

    if matching_rows:
        y = min(matching_rows)
        breadth = PRNG.choice([1, min(3, len(matching_rows))])
        create_h_tunnel(game_map, px, nx, y, breadth)

    elif matching_columns:
        x = min(matching_columns)
        breadth = PRNG.choice([1, min(3, len(matching_columns))])
        create_v_tunnel(game_map, py, ny, x, breadth)

    else:
        arms = PRNG.choice([2, 2, 2, 2, 3, 3, 4])
        breadth = PRNG.choice([1, 3])

        if arms == 2:
            if PRNG.randint(0, 1) == 0:
                create_v_tunnel(game_map, py, ny, px, breadth)
                create_h_tunnel(game_map, px, nx, ny, breadth)

            else:
                create_h_tunnel(game_map, px, nx, py, breadth)
                create_v_tunnel(game_map, py, ny, nx, breadth)

        elif arms == 3:
            if PRNG.randint(0, 1) == 0:
                halfway_y = find_halfway(py, ny)

                create_v_tunnel(game_map, py, halfway_y, px, breadth)
                create_h_tunnel(game_map, px, nx, halfway_y, breadth)
                create_v_tunnel(game_map, halfway_y, ny, nx, breadth)

            else:
                halfway_x = find_halfway(px, nx)

                create_h_tunnel(game_map, px, halfway_x, py, breadth)
                create_v_tunnel(game_map, py, ny, halfway_x, breadth)
                create_h_tunnel(game_map, halfway_x, nx, ny, breadth)

        elif arms == 4:
            if PRNG.randint(0, 1) == 0:
                halfway_y = find_halfway(py, ny)
                halfway_x = find_halfway(px, nx)

                create_v_tunnel(game_map, py, halfway_y, px, breadth)
                create_h_tunnel(game_map, px, halfway_x, halfway_y, breadth)
                create_v_tunnel(game_map, halfway_y, ny, halfway_x, breadth)
                create_h_tunnel(game_map, halfway_x, nx, ny, breadth)

            else:
                halfway_x = find_halfway(px, nx)
                halfway_y = find_halfway(py, ny)

                create_h_tunnel(game_map, px, halfway_x, py, breadth)
                create_v_tunnel(game_map, py, halfway_y, halfway_x, breadth)
                create_h_tunnel(game_map, halfway_x, nx, halfway_y, breadth)
                create_v_tunnel(game_map, halfway_y, ny, nx, breadth)


# TODO: Doc
def create_room(game_map, boundary_x, boundary_y, intersect_chance, room_x=None, room_y=None, square=True):
    while True:
        if not room_x:
            x = PRNG.randint(boundary_x[0], boundary_x[-1])
        else:
            x = room_x

        if not room_y:
            y = PRNG.randint(boundary_y[0], boundary_y[-1])
        else:
            y = room_y

        room = Room(x, y, square=square)

        if room_out_of_bounds(boundary_x, boundary_y, room):
            continue
        else:
            if PRNG.randint(1, 100) > intersect_chance:
                if room_collides(game_map, room):
                    continue
                else:
                    break

    game_map.rooms.append(room)
    room.carve(game_map)
    return room


# TODO: Doc
def find_halfway(pxy, nxy):
    distance = max(pxy, nxy) - min(pxy, nxy)
    halfway = min(pxy, nxy) + int(distance/2)

    return halfway


# TODO: Doc
def room_out_of_bounds(boundary_x, boundary_y, room):
    if boundary_x[0] < room.x1 < room.x2 < boundary_x[-1]:
        pass
    else:
        return True

    if boundary_y[0] < room.y1 < room.y2 < boundary_y[-1]:
        pass
    else:
        return True

    return False


#TODO: Doc
def room_collides(game_map, new_room):
    for y in range(new_room.y1 - 2, new_room.y2 + 2):
        for x in range(new_room.x1 - 2, new_room.x2 + 2):
            if not game_map.viable_coords[x, y]:
                continue
            else:
                return True
    else:
        return False


# TODO: Doc
def create_h_tunnel(game_map, x1, x2, y, h):
    for y in range(y, y + h):
        for x in range(min(x1, x2), max(x1, x2) + h):
            carve_function(game_map, x, y)


# TODO: Doc
def create_v_tunnel(game_map, y1, y2, x, w):
    for x in range(x, x + w):
        for y in range(min(y1, y2), max(y1, y2) + w):
            carve_function(game_map, x, y)


# TODO: Doc
def carve_function(game_map, x, y):
    game_map.transparent[x, y] = True
    game_map.walkable[x, y] = True
    game_map.viable_coords[x, y] = True
    game_map.is_door[x, y] = False
    game_map.door[x][y] = False
    r, g, b = vary_tile_colour(150, 150, 150)
    game_map.set_tile_colour(x, y, (r, g, b))


# TODO: Doc
def set_tile_colour_light_to_dark(game_map, x, y):
    new_r = int(game_map.r[x, y] * 0.6)
    new_g = int(game_map.g[x, y] * 0.6)
    new_b = int(game_map.b[x, y] * 0.6)

    game_map.set_tile_colour(x, y, (new_r, new_g, new_b))


# TODO: doc
def vary_tile_colour(r, g, b):
    variance = PRNG.randint(-25, 25)

    new_r = r + variance
    new_g = g + variance
    new_b = b + variance

    return new_r, new_g, new_b
