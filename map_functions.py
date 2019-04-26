from tdl.map import Map
import numpy as np
import random
from entity_classes import Monster
from render_functions import get_render_char
from entity_classes import stats


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

        self.explored = np.array([[False for y in range(map_height)] for x in range(map_width)])
        self.viable_coords = np.array([[False for y in range(map_height)] for x in range(map_width)])

        self.is_door = np.array([[False for y in range(map_height)] for x in range(map_width)])
        self.door = [[False for y in range(map_height)] for x in range(map_width)]

    def set_door(self, x, y, w=1, h=1, secret=False, button=False):
        """
        This method is typically called during map creation, for the purpose of creating a door in the game map.

        PARAMETERS:
            - x, y (int): the first tile position of the door in the game map.
            - w, h (int): the width and height of the door. Bear in mind that these are absolute, referring to x and y axes.
            - secret (bool): is this door is a normal door (the default, secret being False) or a secret door.
            - button (False or tuple(x, y): is this door can be activated at it's own location, or done via a button.
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

        if secret and w == 1:
            w = 2
        elif secret and h == 1:
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
            button_x, button_y = button
            self.viable_coords[button_x, button_y] = False
            self.transparent[button_x, button_y] = False
            self.walkable[button_x, button_y] = False
            self.is_door[button_x, button_y] = True

            self.door[button_x][button_y] = Button(button_x, button_y, x, y)
            self.door[button_x][button_y].open_char = "/"
            self.door[button_x][button_y].closed_char = "\\"

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

    def carve(self, game_map):
        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):

                game_map.transparent[x, y] = True
                game_map.walkable[x, y] = True
                game_map.viable_coords[x, y] = True


def get_viable_coordinates(game_map):
    """
    Takes the numpy array in game_map representing viable coordinates, and searches for all "True" value indices (x, y).
    Zips these together into individual cartesian coordinates (tuples) in a list.
    Returns this array for use in entity placement functions.
    """
    viable_x, viable_y = np.where(game_map.viable_coords)
    viable_coords = list(zip(viable_x, viable_y))

    return viable_coords


def place_entity(viable_coords, game_map, entity):
    """
    Using a list of viable coordinates from the game map, selects one point at random, and updates the entity's location
    This point is then set to False in GameMap.viable and removed from the viable coords list.

    :param viable_coords: List of viable map coordinates as a tuple i.e. (x, y)
    :param game_map: The GameMap object
    :param entity: The entity to be placed
    """
    random.shuffle(viable_coords)
    place_x, place_y = viable_coords.pop()
    entity.x, entity.y = place_x, place_y
    game_map.viable_coords[place_x, place_y] = False


def create_map(game_map, player, entities):
    """
    Holding function for the map generation routines later on.
    At the moment creates a few simple rects and carves them.

    :param game_map: The game_map object.
    :param player: Player entity object
    """
    room1 = Rect(11, 11, 10, 10)

    v_corridoor_1_2 = Rect(15, 17, 3, 20)
    h_corridoor_1_2 = Rect(15, 36, 10, 3)

    room2 = Rect(25, 31, 20, 10)
    room3 = Rect(30, 11, 10, 10)

    h_corridoor_1_3 = Rect(21, 16, 10, 2)
    v_corridoor_2_3 = Rect(35, 21, 1, 10)

    secret_room_1 = Rect(26, 41, 18, 10)
    secret_room_2 = Rect(31, 7, 8, 4)
    secret_room_3 = Rect(6, 12, 5, 8)

    map_components = [room1, v_corridoor_1_2, h_corridoor_1_2, room2, room3, h_corridoor_1_3, v_corridoor_2_3,
                      secret_room_1, secret_room_2, secret_room_3]

    for component in map_components:
        component.carve(game_map)

    game_map.set_door(15, 21, w=3)
    game_map.set_door(24, 36, h=3)
    game_map.set_door(21, 16, h=2)
    game_map.set_door(29, 16, h=2)
    game_map.set_door(35, 21)
    game_map.set_door(35, 30)
    game_map.set_door(9, 12, w=2, h=8, secret=True)
    game_map.set_door(31, 9, w=8, h=2, secret=True)
    game_map.set_door(26, 41, w=18, h=2, secret=True, button=(30, 35))

    for m in range(random.randint(1, 8)):
        monster_stats = stats(4, 2, 1)
        monster = Monster(0, 0, "Monster", "M", (255, 100, 100), monster_stats)
        entities.append(monster)
        viable_coords = get_viable_coordinates(game_map)
        place_entity(viable_coords, game_map, monster)

    viable_coords = get_viable_coordinates(game_map)
    place_entity(viable_coords, game_map, player)
