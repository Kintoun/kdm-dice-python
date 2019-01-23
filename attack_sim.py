# attack_sim.py
#
# Monte Carlo sims for calculating optimal dice rolls on attacks
import argparse
import copy
import json
import random
import sys


class Weapon(object):
    def __init__(self, name, json_obj):
        self.name = name
        self.speed = json_obj["speed"]
        self.accuracy = json_obj["accuracy"]
        self.strength = json_obj["strength"]
        self.special_mods = {}
        if "special mods" in json_obj:
            self.special_mods = json_obj["special mods"]

    def print_info(self):
        print 'Using weapon \"{0}\" {1}/{2}/{3}'.format(self.name, self.speed, self.accuracy, self.strength)
        if self.special_mods:
            print 'Using special modifiers: [\"{0}\"]'.format('\", \"'.join(self.special_mods))


class Character(object):
    def __init__(self, name, json_obj):
        self.name = name
        self.speed = json_obj["speed"]
        self.accuracy = json_obj["accuracy"]
        self.strength = json_obj["strength"]
        self.fighting_arts = {}
        if "fighting arts" in json_obj:
            self.fighting_arts = json_obj["fighting arts"]

    def print_info(self):
        print 'Using character \"{0}\" +{1} spd, +{2} acc, +{3} str'.format(self.name, self.speed, self.accuracy,
                                                                            self.strength)
        if self.fighting_arts:
            print 'Using fighting arts: [\"{0}\"]'.format('\", \"'.join(self.fighting_arts))


def is_wound(roll, weapon, str, toughness, extra_mods):
    if roll == 1:
        return False
    if roll == 10:
        return True
    if "Sharp" in weapon.special_mods:
        str += random.randint(1, 10)
    wound = roll + str >= toughness
    if wound and "Butcher lv3" in extra_mods:
        butcher_roll = random.randint(1, 10)
        if butcher_roll >= 8:
            wound = False
    return wound


def is_hit(roll, acc):
    return roll == 10 or (roll != 1 and (roll >= acc))


def apply_combomaster(roll):
    count = roll.count(10)
    while count > 0:
        new_roll = random.randint(1, 10)
        roll.append(new_roll)
        if new_roll != 10:
            count -= 1


def roll_n_dice(n):
    roll = []
    for _ in range(n):
        roll.append(random.randint(1, 10))
    return roll


def load_weapon_data(weapon):
    with open("weapon_data.json", "r") as read_file:
        data = json.load(read_file)
        if weapon not in data:
            raise RuntimeError('Weapon not found in weapon_data.json: {0}'.format(weapon))
        return Weapon(weapon, data[weapon])
    return None


def load_character_data(character):
    with open("characters.json", "r") as read_file:
        data = json.load(read_file)
        if character not in data:
            raise RuntimeError('Character not found in characters.json: {0}'.format(character))
        return Character(character, data[character])
    return None


def do_one_attack(weapon, character, toughness, extra_mods):
    spd = weapon.speed + character.speed
    str = weapon.strength + character.strength
    acc = weapon.accuracy - character.accuracy

    auto_wound = False
    savage = "Savage" in weapon.special_mods
    axe_spec = "Axe Spec" in extra_mods or "Axe Spec" in character.fighting_arts

    hit_rolls = roll_n_dice(spd)
    if "Combo Master" in weapon.special_mods:
        apply_combomaster(hit_rolls)
    if "Combo Master" in character.fighting_arts:
        apply_combomaster(hit_rolls)

    if "Mighty Attack 1" in weapon.special_mods:
        for _ in range(hit_rolls.count(10)):
            str += 2
    if "Mighty Attack 1" in character.fighting_arts:
        for _ in range(hit_rolls.count(10)):
            str += 2
    if "Mighty Attack 2" in weapon.special_mods:
        for _ in range(hit_rolls.count(10)):
            str += 4

    if "Early Iron" in weapon.special_mods and 1 in hit_rolls:
        return 0.0, 0.0

    hits = 0.0
    wounds = 0.0
    for hit_roll in hit_rolls:
        if is_hit(hit_roll, acc):
            hits += 1.0
            if ("Counterweighted Axe" in weapon.special_mods and hit_roll == 10) or auto_wound:
                wounds += 1.0
                continue
            wound_roll = random.randint(1, 10)
            if not is_wound(wound_roll, weapon, str, toughness, extra_mods):
                if axe_spec:
                    axe_spec = False
                    wound_roll = random.randint(1, 10)
                    if not is_wound(wound_roll, weapon, str, toughness, extra_mods):
                        continue
                else:
                    continue

            wounds += 1.0
            if "Devastating 1" in weapon.special_mods:
                wounds += 1
            if "Devastating 2" in weapon.special_mods:
                wounds += 2
            # TODO: Not entirely true actually. Only the next wound auto-wounds not all future wounds this atk
            if "Screaming Set" in character.fighting_arts or "Screaming Set" in extra_mods:
                auto_wound = True
            if "Beast Knuckles" in weapon.special_mods:
                toughness -= 1
            if savage and wound_roll == 10:
                wounds += 1.0
                savage = False
    return hits, wounds


def run_attack_sim(weapon, character, toughness, extra_mods, iterations):
    cumhitavg = 0.0
    cumwoundavg = 0.0
    for iteration in range(iterations):
        hits, wounds = do_one_attack(weapon, character, toughness, extra_mods)

        if iteration == 0:
            cumhitavg = hits
            cumwoundavg = wounds
        elif iteration == 1:
            cumhitavg = (hits + cumhitavg) / 2
            cumwoundavg = (wounds + cumwoundavg) / 2
        elif iteration >= 2:
            # Cumulative moving average
            cumhitavg = (cumhitavg * iteration + hits) / (iteration + 1)
            cumwoundavg = (cumwoundavg * iteration + wounds) / (iteration + 1)

    print 'T{0} - Expected hits: {1:.2f}, wounds: {2:.2f}'.format(toughness, cumhitavg, cumwoundavg)


def main():
    parser = argparse.ArgumentParser(prog="attack_sim",
                                     description='Calculate dice rolls for KD:M',
                                     add_help=True)
    parser.add_argument('weapon', type=str, help='The name of the weapon to run the sim on')

    parser.add_argument('--character', type=str, help='The name of the character to use in the sim',
                        default="Default Strength")
    parser.add_argument('--iterations', type=int, help='The number of iterations to run',
                        default=100000)

    # Attacking sim
    parser.add_argument('--toughness', type=int, help='The toughness of the monster', default=0)
    parser.add_argument('--speed', type=int, help='The speed of the attack', default=2)
    parser.add_argument('--hit', type=int, help='The hit value of the attack', default=7)
    parser.add_argument('--strength', type=int, help='The strength of the attack', default=3)
    parser.add_argument('--savage', type=int, help='Weapon has Savage', default=0)
    parser.add_argument('--cwaxe', type=int, help='On perfect hit, auto-wound', default=0)
    parser.add_argument('--devastating', type=int, help='Rank of weapon devastating', default=0)
    parser.add_argument('--scrapsword', type=int, help='On perfect hit, rest of attack is +4 str', default=0)
    parser.add_argument('--mightystrike', type=int, help='On perfect hit, rest of attack is +2 str', default=0)
    parser.add_argument('--screamingset', type=int, help='Activate bonus for Screaming Armor', default=0)
    parser.add_argument('--earlyiron', type=int, help='Weapon has Early Iron', default=0)
    parser.add_argument('--sharp', type=int, help='Weapon has Sharp', default=0)
    parser.add_argument('--combomaster', type=int, help='On perfect hit make 1 additional attack roll', default=0)
    parser.add_argument('--beastknuckles', type=int, help='On wound, monster gains -1 toughness', default=0)
    parser.add_argument('--axe', type=int, help='On wound, attempt to reroll once', default=0)
    parser.add_argument('--butcher', type=int, help='On wound, roll, 8,9,10 wound fails', default=0)

    parser.add_argument('--extra_mods', nargs="*", help='String list of extra mods like axe spec, spear mastery, etc',
                        default='')

    args = parser.parse_args()

    weapon = load_weapon_data(args.weapon)
    character = load_character_data(args.character)
    if weapon and character:
        character.print_info()
        weapon.print_info()
        if args.extra_mods:
            print 'Using extra modifiers: [\"{0}\"]'.format('\", \"'.join(args.extra_mods))

        if args.toughness:
            run_attack_sim(weapon, character, args.toughness, args.extra_mods, args.iterations)
        else:
            run_attack_sim(weapon, character, 10, args.extra_mods, args.iterations)
            #run_attack_sim(weapon, character, 11, args.extra_mods, args.iterations)
            run_attack_sim(weapon, character, 12, args.extra_mods, args.iterations)
            run_attack_sim(weapon, character, 14, args.extra_mods, args.iterations)
            #run_attack_sim(weapon, character, 15, args.extra_mods, args.iterations)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
