from render_functions import RenderOrder
import math
from collections import namedtuple
from message_functions import Message
from config import colours

stats = namedtuple("stats", ["hp", "power", "defense"])


class Entity:
    """
    Entity class is the base class for everything in the game.
    Anything that appears in the game world will naturally have:

        - A position in the game map.
        - A graphical representation (char, colour).
        - A name.

    Map coordinates are passed as integers, char is a single character, colour is an RGB value in a tuple, name is str.

    By default the render order is CORPSE (i.e. the lowest value) and will be rendered on the first pass.
    In effect this means it will likely be rendered on top of by other more important entities (Actors, items).
    """
    def __init__(self, map_x, map_y, name, char, colour):
        self.x = map_x
        self.y = map_y
        self.name = name
        self.char = char
        self.colour = colour
        self.blocks = False
        self.render_order = RenderOrder.CORPSE


class Actor(Entity):
    """
    Actors include anything in the game which can independently affect the game world.
    The player, monsters, and NPCs are actors, and as such they share some common behaviours such as movement.
    """
    def __init__(self, map_x, map_y, name, char, colour, stats):
        super().__init__(map_x, map_y, name, char, colour)
        self.render_order = RenderOrder.ACTOR
        self.blocks = True
        self.max_hp = stats.hp
        self.hp = stats.hp
        self.power = stats.power
        self.defense = stats.defense

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def take_damage(self, amount):
        results = []

        self.hp -= amount

        if self.hp <= 0:
            results.append({"dead": self})

        return results

    def attack(self, target):
        results = []

        damage = self.power - target.defense

        if damage > 0:
            results.append({"message": Message("{} takes {} damage from {}"
                           .format(target.name, damage, self.name, target.hp), colours["light_red"])})
            results.extend(target.take_damage(damage))

        else:
            results.append({"message": Message("{} attacks {} but does no damage".format(self.name, target.name), colours["red"])})

        return results


class Item(Entity):
    """
    Items are entities which are static in the game world until come across by actors.
    All items share some common behaviours such as the ability to be picked up, activated/used, and stored in inventory.
    """
    def __init__(self, map_x, map_y, name, char, colour):
        super().__init__(map_x, map_y, name, char, colour)
        self.render_order = RenderOrder.ITEM


class Player(Actor):
    """
    The player is a specific type of Actor which can be controlled by the user.
    There will be some unique functions here later which other actors should not have access to.
    """
    def __init__(self, map_x, map_y, name, char, colour, stats):
        super().__init__(map_x, map_y, name, char, colour, stats)

        if len(name) > 15:
            self.name = name[0:15]


# TODO: doc
class Monster(Actor):
    """
    The monster is an actor which is not controlled by the user.
    This class will contain AI routines for independent movement and other expected behaviours such as combat.
    """
    def __init__(self, map_x, map_y, name, char, colour, stats):
        super().__init__(map_x, map_y, name, char, colour, stats)
        self.dead = False

    def move_towards(self, target_x, target_y, game_map, entities):
        path = game_map.compute_path(self.x, self.y, target_x, target_y)

        dx = path[0][0] - self.x
        dy = path[0][1] - self.y

        if game_map.walkable[path[0][0], path[0][1]] and not get_blocking_entities_at_location(entities, self.x + dx, self.y + dy):
            self.move(dx, dy)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def take_turn(self, target, game_map, entities):
        results = []

        if game_map.fov[self.x, self.y]:
            if self.distance_to(target) >= 2:
                self.move_towards(target.x, target.y, game_map, entities)

            elif target.hp > 0:
                attack_results = self.attack(target)
                results.extend(attack_results)

        return results


# TODO: doc
def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None
