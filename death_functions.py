from game_states import GameStates
from render_functions import RenderOrder
from message_functions import Message
from config import colours


def kill_player(player):
    player.char = "%"
    player.colour = (127, 0, 0)

    return Message("You died", colours["dark_red"]), GameStates.PLAYER_DEAD


def kill_monster(monster):
    death_message = Message("{} is dead!".format(monster.name), colours["dark_red"])

    monster.dead = True
    monster.name = "Remains of {}".format(monster.name.capitalize())
    monster.char = "%"
    monster.colour = (127, 0, 0)
    monster.blocks = False
    monster.render_order = RenderOrder.CORPSE

    return death_message

