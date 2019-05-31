from map_functions import GameMap, carve_function
from entity_classes import Monster, stats


def gen_blank_file(filename, map_width, map_height):
    with open(filename, "w") as blank_map:
        for y in range(map_height):
            for x in range(map_width):
                print("#", end='', file=blank_map)
            print("", file=blank_map)


def read_map_from_file(filename, player, entities):
    grid = []

    with open(filename, "r") as new_map:
        rows = [line.rstrip("\n") for line in new_map]
        for row in rows:
            grid.append([char for char in row])

    map_width = len(grid[0])
    map_height = len(grid)
    game_map = GameMap(map_width, map_height)
    monster_stats = stats(hp=2, power=1, defense=1)

    buttons = dict()

    for y in range(map_height):
        for x in range(map_width):
            tile = grid[y][x]

            if tile == "{":
                carve_function(game_map, x, y)
                buttons[tile] = (x, y, (255, 255, 0))

            if tile == "[":
                carve_function(game_map, x, y)
                buttons[tile] = (x, y, (114, 255, 114))

            if tile == "(":
                carve_function(game_map, x, y)
                buttons[tile] = (x, y, (114, 114, 255))

    for y in range(map_height):
        for x in range(map_width):
            tile = grid[y][x]

            if tile == "#":
                pass
            elif tile == ".":
                carve_function(game_map, x, y)
            elif tile == "p":
                carve_function(game_map, x, y)
                player.x, player.y = x, y
            elif tile == "+":
                game_map.set_door(x, y)
            elif tile == "?":
                game_map.set_door(x, y, secret=True)
            elif tile == "m":
                carve_function(game_map, x, y)
                monster = Monster(x, y, "Monster", "M", (255, 50, 50), monster_stats)
                entities.append(monster)

            elif tile == "}":
                game_map.set_door(x, y, button=buttons["{"])
            elif tile == "]":
                game_map.set_door(x, y, button=buttons["["])
            elif tile == ")":
                game_map.set_door(x, y, button=buttons["("])

    return game_map
