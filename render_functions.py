from enum import Enum
import tdl
import numpy as np
from config import colours
from game_states import GameStates


class RenderOrder(Enum):
    """
    Simple class containing render order types.
    """
    CORPSE = 1
    ITEM = 2
    ACTOR = 3


def render_all(game_map, all_consoles, player, entities, fov_recompute, screen_layout, message_log, mouse_coordinates):
    """
    Draw all game elements on screen. This function is called from the engine every frame.
    This actually just calls the individual functions to draw the map, game entities, and other HUD elements.

    Console info:
        - map console (where the map and entities are drawn)
        - view port console (where the currently visible portion of the map is drawn to)
        - root console (where the view port and later the HUD panel consoles will be drawn.

    The root console is the only one actually drawn to the screen.
    """

    # Unpack all consoles.
    root_console, view_port_console, map_console, message_console, hud_console = all_consoles

    # Unpack screen layout
    view_port_width, view_port_height = screen_layout["view_port"]
    message_log_width, message_log_height = screen_layout["message_log"]
    hud_width, hud_height = screen_layout["hud"]

    # Re-draw graphics if the fov recompute trigger has been set.
    if fov_recompute:
        draw_map(game_map, map_console, player, view_port_width, view_port_height)  # Draw the map
        draw_entities(game_map, map_console, entities)  # Draw the game entities
        draw_message_log(message_console, message_log)  # Draw the message log
        draw_hud(hud_console, player)

        # Update the root console
        update_display(game_map, player,
                       root_console, view_port_console, map_console, message_console, hud_console,
                       view_port_width, view_port_height, message_log_width, message_log_height, hud_width, hud_height)

    # Clear entities from the map console ready for update next frame.
    clear_all(map_console, entities)


def draw_hud(hud_console, player):
    hud_console.draw_str(0, 0, player.name, bg=None, fg=colours["white"])
    render_status_bar(hud_console, 17, 0, 10, player.hp, player.max_hp, colours["light_red"], colours["dark_red"])


def draw_message_log(message_console, message_log):
    """
    :param message_console: The console used to display the message log on screen.
    :param message_log: The message_log object which stores the individual message objects to be drawn.
    """
    # Print the game messages, one line at a time
    y = message_log.y
    for message in message_log.messages:
        message_console.draw_str(message_log.x, y, message.text, bg=None, fg=message.colour)
        y += 1


def get_render_char(game_map, x, y):
    """
    Takes the x, y coordinate of the tile to be drawn (Td), and based on surrounding neighbours will calculate a unique
    value integer which acts as the dict key to lookup the ASCII constant to be drawn (the values in the dict).

    Each type of tile (horizontal, vertical walls / corners) will have a unique arrangement of transparent and
    non-transparent tiles surrounding it. For each tile in the 9-tile cell, the mask value is added for that position
    in the cell only if that tile is transparent.

    This is essentially bitmasking.

    :param game_map: the game_map object
    :param x: coordinate of tile to be drawn
    :param y: as above
    :return: the ASCII constant of the tile to be drawn.

    This function will be used to grab the console character for:
        - Walls
        - Doors
        - Floor

    First we will return either the door char or the floor char if either is relevant. Failing the above, go through the
    bitmasking process to ascertain which wall char should be returned.
    """

    # If this tile is a door, then "this_door" points to the Door object for it.
    if game_map.is_door[x, y]:
        this_door = game_map.door[x][y]

        # If that door is not a secret door, we can safely return the default open/close chars stored in the Door object
        if not this_door.secret:

            if this_door.is_open:
                return this_door.open_char
            else:
                return this_door.closed_char

        # If it IS a secret door...
        else:
            # If it's open we can drawn it's open char (secret door open chars are assigned as 197 (floor) when created)
            if this_door.is_open:
                return this_door.open_char

            # If the secret door is closed we need to figure out which char should be drawn as if it were a wall

    # If the tile is not a door at all, and it's transparent, then it's the floor. Draw that.
    elif game_map.transparent[x, y]:
        return 197

    '''
    At this point things start to get a little technical. If the tile is not a door and is not the floor then its a wall
    and we need to figure out which particular type of wall tile it should be based on it's neighbours.
    '''

    # First create a 2d list array (3x3) of tuples containing the coordinates surrounding the tile to be drawn (Td).
    cell = [[(xcoord, ycoord) for ycoord in range(y - 1, y + 2)] for xcoord in range(x - 1, x + 2)]

    # Create a 3x3 mask corresponding to the 9 tile cell - values should be exponential to ensure no tile combination
    # produces a duplicate value when summed together. This current set of values does not achieve this in all cases.
    mask = np.array([[1, 3, 9], [10, 30, 90], [100, 300, 900]])

    # The cell map is another 3x3 array False by default, then each transparent cell on the game map is set to True.
    cell_map = np.array([[False for y in range(3)] for x in range(3)])
    for ypos in range(3):
        for xpos in range(3):
            map_x, map_y = cell[ypos][xpos]
            try:
                if game_map.transparent[map_x, map_y]:
                    cell_map[xpos, ypos] = True

            except IndexError:
                pass

    # For each transparent tile in the cell map, use the mask value for that cell position, otherwise it's 0.
    cell_map_masked = np.zeros((3, 3))
    for ypos in range(3):
        for xpos in range(3):
            if cell_map[xpos, ypos]:
                cell_map_masked[xpos, ypos] = mask[xpos, ypos]

    # Add up all the mask values for this cell - this will act as the dictionary key to pull the ASCII to be drawn.
    char_key = int(np.sum(cell_map_masked))

    '''
    Below are all the masked values currently being used by the auto-tiler (keys) against the relevant ASCII constant
    which will be later passed to the draw_map function (or a Door object). For complicated map layours (such as caves)
    or really anything that isn't derived from Rects, i fully expect this to break down.
    '''

    chars = dict()
    # Horizontal wall
    chars[1300] = 205
    chars[13] = 205
    chars[400] = 205
    chars[1200] = 205
    chars[4] = 205
    chars[12] = 205
    chars[1313] = 205
    chars[1212] = 205
    chars[404] = 205
    # Vertical wall
    chars[999] = 186
    chars[111] = 186
    chars[990] = 186
    chars[99] = 186
    chars[110] = 186  # DUPLICATE combination works for two layouts
    chars[11] = 186
    chars[1110] = 186
    chars[1100] = 186
    # Top Left corner
    chars[900] = 201
    chars[123] = 201
    chars[113] = 201
    chars[120] = 201
    chars[23] = 201
    chars[114] = 201
    # Top Right corner
    chars[100] = 187
    chars[1003] = 187
    chars[913] = 187
    chars[1000] = 187
    chars[1002] = 187
    chars[103] = 187
    # Bottom Left corner
    chars[9] = 200
    chars[1311] = 200
    chars[1011] = 200
    chars[1301] = 200
    chars[1310] = 200
    chars[411] = 200
    # Bottom Right corner
    chars[1] = 188
    chars[1399] = 188
    chars[1099] = 188
    chars[1309] = 188
    chars[1299] = 188
    chars[1390] = 188

    '''
    Try to return a value from the dict above.
    If the key doesn't exist, draw a block char and print an error message.
    I've negated the value of 0 because this relates to the instance when all surrounding tiles are walls - which occurs
    on a large proportion of the non-visible map tiles behind walls.
    '''

    try:
        return chars[char_key]

    except KeyError:
        if char_key != 0:
            print("Get wall tile key error: ", char_key, x, y)
        return 176


def draw_map(game_map, map_console, player, view_port_width, view_port_height):
    """
    A function to render the map on screen. Iterates through the game_map tiles taking player FOV into account and
    draws the contents to the map console which will later be passed to the root console via another function.

    :param game_map: The game map object.
    :param map_console: This console ONLY draws the map, a portion of this console is blitted based on current view_port
    :param player: Player entity object.
    :param view_port_width: The width of the view_port in the screen layout.
    :param view_port_height: As above
    """

    # This grabs the view port coordinates. See function docstring for more detailed info.
    view_port_x1, view_port_y1, view_port_x2, view_port_y2 = get_view_port_position(player, game_map, view_port_width, view_port_height)

    # Iterate through the tiles in the game_map object to draw them
    for x, y in game_map:

        # Only draw the tile if it appears within the constraints of the view port.
        if view_port_x1 <= x < view_port_x2 and view_port_y1 <= y < view_port_y2:

            '''
            First we create a condition to check whether the current tile is the ground (if it's transparent)
            then pull the char for this tile using the auto-tile function (get_render_char).
            '''

            ground = game_map.transparent[x, y]
            char = get_render_char(game_map, x, y)

            # Set the colours based on whether it's the ground or non-ground (walls and doors are the same colour.
            if ground:
                light_colour = (150, 150, 150)
                dark_colour = (75, 75, 75)
            else:
                light_colour = (250, 250, 250)
                dark_colour = (125, 125, 125)

            # If the tile is within the FOV, draw it with the light colours, if it's outside FOV and explored, use dark
            if game_map.fov[x, y]:
                map_console.draw_char(x, y, char, fg=light_colour, bg=None)
                game_map.explored[x, y] = True

            elif game_map.explored[x, y]:
                map_console.draw_char(x, y, char, fg=dark_colour, bg=None)


# TODO: Doc
def draw_entities(game_map, map_console, entities):
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)

    for entity in entities_in_render_order:
        draw_entity(map_console, entity, game_map.fov)


# TODO: Doc
def update_display(game_map, player, root_console, view_port_console, map_console, message_console, hud_console,
                   view_port_width, view_port_height, message_log_width, message_log_height, hud_width, hud_height):

    view_port_x1, view_port_y1, _, _ = get_view_port_position(player, game_map, view_port_width, view_port_height)

    view_port_console.blit(map_console, 0, 0, srcX=view_port_x1, srcY=view_port_y1, width=view_port_width, height=view_port_height)
    root_console.blit(view_port_console, 2, 10, view_port_width, view_port_height, 0, 0)
    view_port_console.clear()

    root_console.blit(message_console, 2, 42, width=message_log_width, height=message_log_height)
    message_console.clear()

    root_console.blit(hud_console, 2, 2, width=hud_width, height=hud_height)
    hud_console.clear()

    tdl.flush()


# TODO: Doc, this may not work in this game
def render_status_blocks(panel, x, y, current_value, maximum_value, fg_colour, bg_colour):
    x = x
    for i in range(maximum_value):
        panel.draw_str(x, y, " ", None, bg_colour)
        if current_value - 1 >= i:
            panel.draw_str(x, y, " ", None, fg_colour)
        x += 2


# TODO: Doc, this may not work in this game
def render_status_characters(panel, x, y, current_value, maximum_value, char_code, fg_colour, bg_colour):
    x = x
    for i in range(maximum_value):
        panel.draw_char(x, y, char_code, bg_colour, None)
        if current_value - 1 >= i:
            panel.draw_char(x, y, char_code, fg_colour, None)
        x += 2


# TODO: Doc, this may not work in this game
def render_status_bar(panel, x, y, width, current_value, maximum_value, bar_colour, back_colour):
    if maximum_value == 0:
        bar_width = width
    else:
        bar_width = int(float(current_value) / maximum_value * width)

        if bar_width == 0 and current_value > 0:  # This avoids rounding errors if bar disappears but the value isn't 0
            bar_width = 1

    # draw background
    panel.draw_rect(x , y, width, 1, None, bg=back_colour)

    # draw the remaining total bar on top
    if bar_width > 0:
        panel.draw_rect(x, y, bar_width, 1, None, bg=bar_colour)


# TODO: Doc
def get_view_port_position(player, game_map, view_port_width, view_port_height):
    view_port_x1 = player.x - int(view_port_width * 0.5)
    view_port_y1 = player.y - int(view_port_height * 0.5)
    view_port_x2 = view_port_x1 + view_port_width
    view_port_y2 = view_port_y1 + view_port_height

    if view_port_x2 > game_map.width:
        view_port_x1 = game_map.width - 30
    elif view_port_x1 < 0:
        view_port_x1 = 0

    if view_port_y2 > game_map.height:
        view_port_y1 = game_map.height - 30
    elif view_port_y1 < 0:
        view_port_y1 = 0

    return view_port_x1, view_port_y1, view_port_x2, view_port_y2


# TODO: the "-2" may be wrong on these functions as they're from another project. Check later.
def screen_from_map(map_x, map_y, view_port_x1, view_port_y1):
    screen_x = map_x - (view_port_x1 - 2)
    screen_y = map_y - (view_port_y1 - 2)

    return screen_x, screen_y


# TODO: as above
def map_from_screen(screen_x, screen_y, view_port_x1, view_port_y1):
    map_x = screen_x + (view_port_x1 - 2)
    map_y = screen_y + (view_port_y1 - 10)

    return map_x, map_y


# TODO: Doc
def clear_all(map_console, entities):
    for entity in entities:
        clear_entity(map_console, entity)


# TODO: Doc
def draw_entity(map_console, entity, fov):
    if fov[entity.x, entity.y]:
        map_console.draw_char(entity.x, entity.y, entity.char, entity.colour, bg=None)


# TODO: Doc
def clear_entity(map_console, entity):
    map_console.draw_char(entity.x, entity.y, ' ', entity.colour, bg=None)
