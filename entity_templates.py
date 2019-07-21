from entity_classes import Monster, stats
from collections import namedtuple

monster_template = namedtuple("monster", ["name", "char", "colour", "stats"])

# Player: hp=200, arm=50, mp=25, str=4, dex=2


# Level 1
imp = monster_template("Imp", "i", (255, 50, 50), stats(hp=4, arm=8, mp=0, str=8, dex=2))
goblin = monster_template("Goblin", "g", (100, 200, 50), stats(hp=6, arm=10, mp=0, str=12, dex=3))
rat = monster_template("Rat", "r", (200, 100, 100), stats(hp=2, arm=0, mp=0, str=4, dex=1))
kobold = monster_template("Kobold", "k", (120, 250, 160), stats(hp=5, arm=8, mp=0, str=6, dex=2))

# Level 2
goblin_fighter = monster_template("Goblin Fighter", "g", (75, 150, 25), stats(hp=10, arm=20, mp=0, str=15, dex=6))

# Monster Manual
monster_manual = dict()
monster_manual["level1"] = (imp, goblin, rat, kobold)
monster_manual["kobolds"] = (kobold)
monster_manual["demons"] = (imp)
monster_manual["critters"] = (rat)
monster_manual["orcs/goblins"] = (goblin, goblin_fighter)
