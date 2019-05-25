import tdl
from game_states import GameStates
from input_functions import handle_keys
from map_functions import GameMap, make_map, create_set_map, Button
from entity_classes import Monster, Player, get_blocking_entities_at_location, stats
from render_functions import render_all
from message_functions import MessageLog
from death_functions import kill_player, kill_monster
from config import colours


def main():
    # # SET GAME CONSTANTS
    # Map - any width and height OK, view port will move with player.
    map_width, map_height = (150, 150)

    # View Port - the area of the screen displaying game world.
    view_port_width, view_port_height = (30, 30)

    # Screen = derive from view port. Leave 2 cells at each side (if no side panels), 10 at top and bottom for HUD.
    screen_width = view_port_width + 19
    screen_height = view_port_height + 24

    # Message log (bottom panel)
    message_log_width, message_log_height = (screen_width - 4, 8)

    # HUD (top panel)
    hud_width, hud_height = (screen_width - 4, 10)

    # Dict to contain screen architecture
    screen_layout = dict()
    screen_layout["screen"] = (screen_width, screen_height)
    screen_layout["map"] = (map_width, map_height)
    screen_layout["view_port"] = (view_port_width, view_port_height)
    screen_layout["message_log"] = (message_log_width, message_log_height)
    screen_layout["hud"] = (hud_width, hud_height)

    # # INITIALISE TDL CONSOLE ENGINE
    # General - set the font to be used, and fps limit.
    tdl.set_font('terminal16x16.png', greyscale=True, altLayout=False)
    tdl.set_fps(100)

    # Consoles - these are different drawing canvases. Root is what is displayed on screen, pulled from other consoles.
    root_console = tdl.init(screen_width, screen_height, title='Roguelike 3')
    map_console = tdl.Console(map_width, map_height)
    message_console = tdl.Console(message_log_width, message_log_height)
    view_port_console = tdl.Console(view_port_width, view_port_height)
    hud_console = tdl.Console(hud_width, hud_height)

    # Holding list to be unpacked in render function.
    all_consoles = [root_console, view_port_console, map_console, message_console, hud_console]

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
    mouse_coordinates = (0, 0)

    # Player & entities - set up player stats, then put in holding list for all game entities.
    player_stats = stats(50, 2, 1)
    player = Player(5, 5, "Bolly Angerfist", "@", (255, 255, 255), player_stats)
    entities = [player]

    # Map - create the map object, and then run the function to generate game world.
    game_map = GameMap(map_width, map_height)
    make_map(game_map, player, num_rooms=20, min_size=5, max_size=15, map_border=3, intersect_chance=10)
    # create_set_map(game_map, player, entities)

    # # MAIN GAME LOOP
    while not tdl.event.is_window_closed():  # Endless loop while program is still running

        '''RENDERING START'''
        # Recompute the FOV around the player only when triggered.
        if fov_recompute:
            game_map.compute_fov(player.x, player.y,
                                 fov=fov_algorithm, radius=fov_radius, light_walls=fov_light_walls, sphere=True)

        # Main rendering function - perform every frame.
        render_all(game_map, all_consoles, player, entities, fov_recompute, screen_layout, message_log, mouse_coordinates)
        fov_recompute = False
        '''RENDERING END'''

        '''GET INPUT START'''
        # Check for keyboard/mouse events.
        for event in tdl.event.get():
            if event.type == 'KEYUP':
                user_input = event
                break

            elif event.type == "MOUSEMOTION":
                mouse_coordinates = event.cell

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
        '''GET INPUT END'''

        '''MENU HANDLING START'''
        if exit_game:
            return True  # Break out of the loop and close script.

        if fullscreen:
            tdl.set_fullscreen(not tdl.get_fullscreen())
        '''MENU HANDLING END'''

        '''PLAYER TURN START'''
        player_turn_results = []

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
                        attack_results = player.attack(target)
                        player_turn_results.extend(attack_results)
                        fov_recompute = True

                else:
                    player.move(dx, dy)
                    fov_recompute = True

            # If the tile is a door and not open, and not a door with a button - open it when touched by player.
            elif game_map.is_door[destination_x, destination_y] and not game_map.door[destination_x][destination_y].is_open:
                if not game_map.door[destination_x][destination_y].button:
                    game_map.open_door(destination_x, destination_y)
                    fov_recompute = True

                # If the tile is a Button, activate it.
                if isinstance(game_map.door[destination_x][destination_y], Button):
                    game_map.door[destination_x][destination_y].open_door(game_map)
                    fov_recompute = True

            game_state = GameStates.ENEMY_TURN

        for result in player_turn_results:
            message = result.get("message")
            dead_entity = result.get("dead")

            if message:
                message_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)

                message_log.add_message(message)
        '''PLAYER TURN END'''

        '''ENEMY TURN START'''
        # If this is the Enemy's turn, iterate through the entities list and let the Monster objects take an action.
        if game_state == GameStates.ENEMY_TURN:

            for entity in entities:
                if isinstance(entity, Monster) and not entity.dead:
                    enemy_turn_results = entity.take_turn(player, game_map, entities)
                    fov_recompute = True

                    for result in enemy_turn_results:
                        message = result.get("message")
                        dead_entity = result.get("dead")

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)

                            message_log.add_message(message)

                        if game_state == GameStates.PLAYER_DEAD:
                            break

                    if game_state == GameStates.PLAYER_DEAD:
                        break

            else:
                game_state = GameStates.PLAYER_TURN
            '''ENEMY TURN START'''


if __name__ == "__main__":
    main()
