from render_functions import RenderOrder
import math
from collections import namedtuple
from message_functions import Message
from config import colours
from random import randint

stats = namedtuple("stats", ["hp", "arm", "mp", "str", "dex"])


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
        self.id = id(self)


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
        self.max_arm = stats.arm
        self.arm = stats.arm
        self.max_mp = stats.mp
        self.mp = stats.mp
        self.str = stats.str
        self.dex = stats.dex

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

        self_crit_roll = randint(1, 20)
        target_crit_roll = randint(1, 20)

        if self_crit_roll == 1:
            attack_power = randint(int(self.str * 0.25), int(self.str * 0.5))
        elif self_crit_roll == 20:
            attack_power = randint(int(self.str * 1), int(self.str * 1.25))
        else:
            attack_power = randint(int(self.str * 0.75), int(self.str * 1))

        if target_crit_roll == 1:
            dodge = randint(int(target.dex * 0), int(target.dex * 0.25))
        elif self_crit_roll == 20:
            dodge = randint(int(target.dex * 0.75), int(target.dex * 1))
        else:
            dodge = randint(int(target.dex * 0.5), int(target.dex * 0.75))

        damage = attack_power - dodge

        if damage > 0:
            results.append({"message": Message("{} attacks for {} damage"
                           .format(self.name, damage), self.colour)})
            results.extend(target.take_damage(damage))

        else:
            results.append({"message": Message("{} attacks but does no damage".format(self.name), self.colour)})

        return results


class Item(Entity):
    """
    Items are entities which are static in the game world until come across by actors.
    All items share some common behaviours such as the ability to be picked up, activated/used, and stored in inventory.
    """
    def __init__(self, map_x, map_y, name, char, colour):
        super().__init__(map_x, map_y, name, char, colour)
        self.render_order = RenderOrder.ITEM


class Pickup(Item):
    def __init__(self, map_x, map_y, name, char, colour, stats):
        super().__init__(map_x, map_y, name, char, colour)

        self.hp = stats.hp
        self.arm = stats.arm
        self.mp = stats.mp
        self.str = stats.str
        self.dex = stats.dex

    def activate(self, target, entities):
        results = list()
        results.append({"message": Message("{} picks up {}".format(target.name, self.name), self.colour)})

        used = False

        if self.hp > 0:
            if target.hp == target.max_hp:
                results.append({"message": Message("HP already full!", self.colour)})
            elif (target.hp + self.hp) > target.max_hp:
                results.append({"message": Message("{} HP restored.".format(target.max_hp - target.hp), self.colour)})
                target.hp = target.max_hp
                used = True
            else:
                results.append({"message": Message("{} HP restored.".format(self.hp), self.colour)})
                target.hp += self.hp
                used = True

        if self.mp > 0:
            if target.mp == target.max_mp:
                results.append({"message": Message("MP already full!", self.colour)})
            elif (target.mp + self.mp) > target.max_mp:
                results.append({"message": Message("{} MP restored.".format(target.max_mp - target.mp), self.colour)})
                target.mp = target.max_mp
                used = True
            else:
                results.append({"message": Message("{} MP restored.".format(self.mp), self.colour)})
                target.mp += self.mp
                used = True

        if self.arm > 0:
            if target.arm == target.max_arm:
                results.append({"message": Message("AR already full!", self.colour)})
            elif (target.arm + self.arm) > target.max_arm:
                results.append({"message": Message("{} AR restored.".format(target.max_arm - target.arm), self.colour)})
                target.arm = target.max_arm
                used = True
            else:
                results.append({"message": Message("{} AR restored.".format(self.arm), self.colour)})
                target.arm += self.arm
                used = True

        if used:
            entities.remove(self)

        return results


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
