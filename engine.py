import tdl
from game_states import GameStates
from input_functions import handle_keys
from map_functions import GameMap, create_map, Button
from entity_classes import Monster, Player, get_blocking_entities_at_location
from render_functions import render_all
from message_functions import MessageLog, Message


def main():
    # # SET GAME CONSTANTS
    # Map - any width and height OK, view port will move with player.
    map_width, map_height = (100, 100)

    # View Port - the area of the screen displaying game world.
    view_port_width, view_port_height = (30, 30)

    # Screen = derive from view port. Leave 2 cells at each side (if no side panels), 10 at top and bottom for HUD.
    screen_width = view_port_width + 19
    screen_height = view_port_height + 24

    # Message log (bottom panel)
    message_log_width, message_log_height = (screen_width - 4, 10)

    # Dict to contain screen architecture
    screen_layout = dict()
    screen_layout["screen"] = (screen_width, screen_height)
    screen_layout["map"] = (map_width, map_height)
    screen_layout["view_port"] = (view_port_width, view_port_height)
    screen_layout["message_log"] = (message_log_width, message_log_height)

    # # INITIALISE TDL CONSOLE ENGINE
    # General - set the font to be used, and fps limit.
    tdl.set_font('terminal16x16.png', greyscale=True, altLayout=False)
    tdl.set_fps(100)

    # Consoles - these are different drawing canvases. Root is what is displayed on screen, pulled from other consoles.
    root_console = tdl.init(screen_width, screen_height, title='Roguelike 3')
    map_console = tdl.Console(map_width, map_height)
    message_console = tdl.Console(message_log_width, message_log_height)
    view_port_console = tdl.Console(view_port_width, view_port_height)

    # Holding list to be unpacked in render function.
    all_consoles = [root_console, view_port_console, map_console, message_console]

    # Set up HUD panels
    message_log = MessageLog(0, 0, width=message_log_width, height=message_log_height)

    # Field of view configuration
    fov_algorithm = "BASIC"
    fov_light_walls = True
    fov_radius = 10
    fov_recompute = True

    # # GAME WORLD SETUP
    # General - set the initial game state.
    game_state = GameStates.PLAYER_TURN

    # Player & entities - set up player stats, then put in holding list for all game entities.
    player = Player(5, 5, "Player", "@", (255, 255, 255))
    entities = [player]

    # Map - create the map object, and then run the function to generate game world.
    game_map = GameMap(map_width, map_height)
    create_map(game_map, player, entities)

    # # MAIN GAME LOOP
    while not tdl.event.is_window_closed():  # Endless loop while program is still running
        # Recompute the FOV around the player only when triggered.
        if fov_recompute:
            game_map.compute_fov(player.x, player.y,
                                 fov=fov_algorithm, radius=fov_radius, light_walls=fov_light_walls, sphere=True)

        # Main rendering function - perform every frame.
        render_all(game_map, all_consoles, player, entities, fov_recompute, screen_layout, message_log)
        fov_recompute = False

        # Check for keyboard/mouse events.
        for event in tdl.event.get():
            if event.type == 'KEYUP':
                user_input = event
                break

        else:
            user_input = None

        if not user_input:
            continue

        # Take the keyboard input and parse through the input handler.
        action = handle_keys(user_input)

        # Get actions only of the type indicated by the input handler.
        move = action.get('move')
        exit_game = action.get('exit_game')
        fullscreen = action.get('fullscreen')
        message = action.get('message')

        if message:
            message_log.add_message(Message("Message message message message message message"))
            fov_recompute = True

        # If it's a movement event and it's the player's turn, move the player.
        if move and game_state == GameStates.PLAYER_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy

            # Only move the player if its a walkable tile on the map.
            if game_map.walkable[destination_x, destination_y]:
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)

                if target:
                    if isinstance(target, Monster):
                        pass
                        # Combat here

                else:
                    player.move(dx, dy)
                    fov_recompute = True

            # TODO: Doc
            elif game_map.is_door[destination_x, destination_y] and not game_map.door[destination_x][destination_y].is_open:
                if not game_map.door[destination_x][destination_y].button:
                    game_map.open_door(destination_x, destination_y)
                    fov_recompute = True

                if isinstance(game_map.door[destination_x][destination_y], Button):
                    game_map.door[destination_x][destination_y].open_door(game_map)
                    fov_recompute = True

            game_state = GameStates.ENEMY_TURN

        if exit_game:
            return True  # Break out of the loop and close script.

        if fullscreen:
            tdl.set_fullscreen(not tdl.get_fullscreen())

        # TODO: doc
        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if isinstance(entity, Monster):
                    entity.take_turn(player, game_map, entities)

            else:
                game_state = GameStates.PLAYER_TURN


if __name__ == "__main__":
    main()
