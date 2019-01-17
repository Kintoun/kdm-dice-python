# attack_sim.py
#
# Monte Carlo sims for calculating optimal dice rolls on attacks
import argparse
import copy
import json
import random
import sys


class Weapon(object):
    def __init__(self, json_obj):
        self.speed = json_obj["speed"]
        self.accuracy = json_obj["accuracy"]
        self.strength = json_obj["strength"]
        self.special_mods = json_obj["special mods"]


def is_wound(roll, weapon, toughness, extra_mods):
    strength = weapon.strength
    if roll == 1:
        return False
    if roll == 10:
        return True
    if "Sharp" in weapon.special_mods:
        strength += random.randint(1, 10)
    wound = roll + strength >= toughness
    if wound and "Butcher" in extra_mods:
        butcher_roll = random.randint(1, 10)
        if butcher_roll >= 8:
            wound = False
    return wound


def is_hit(roll, weapon):
    return roll == 10 or (roll != 1 and (roll >= weapon.accuracy))


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
        if not data[weapon]:
            raise RuntimeError('Weapon not found in weapon_data.json: {0}'.format(weapon))
        return Weapon(data[weapon])
    return None


def do_one_attack(weap, toughness, extra_mods):
    # Snapshot weapon data to isolate any modifiers
    weapon = copy.deepcopy(weap)
    hit_rolls = roll_n_dice(weapon.speed)
    if "Combo Master" in weapon.special_mods:
        apply_combomaster(hit_rolls)
    hits = 0.0
    wounds = 0.0
    auto_wound = False
    savage = "Savage" in weapon.special_mods
    axe_spec = "Axe Spec" in extra_mods
    if "Mighty Attack 1" in weapon.special_mods:
        for _ in range(hit_rolls.count(10)):
            weapon.strength += 2
    if "Mighty Attack 2" in weapon.special_mods:
        for _ in range(hit_rolls.count(10)):
            weapon.strength += 4

    if "Early Iron" in weapon.special_mods and 1 in hit_rolls:
        return 0.0, 0.0

    for hit_roll in hit_rolls:
        if is_hit(hit_roll, weapon):
            hits += 1.0
            if ("Counter-weight Axe" in weapon.special_mods and hit_roll == 10) or auto_wound:
                wounds += 1.0
                continue
            wound_roll = random.randint(1, 10)
            if not is_wound(wound_roll, weapon, toughness, extra_mods):
                if axe_spec:
                    axe_spec = False
                    wound_roll = random.randint(1, 10)
                    if not is_wound(wound_roll, weapon.strength, toughness, extra_mods):
                        continue
                else:
                    continue

            wounds += 1.0
            if "Devastating 1" in weapon.special_mods:
                wounds += 1
            if "Devastating 2" in weapon.special_mods:
                wounds += 2
            if "Screaming Set" in extra_mods:
                auto_wound = True
            if "Beast Knuckles" in weapon.special_mods:
                toughness -= 1
            if savage and wound_roll == 10:
                wounds += 1.0
                savage = False
    return hits, wounds


def run_attack_sim(weapon, toughness, extra_mods, iterations):
    print 'Calculating attack for {0}/{1}/{2} attack against {3} toughness at {4} iterations'.format(
        weapon.speed, weapon.accuracy, weapon.strength, toughness, iterations)
    if extra_mods:
        print 'Using extra modifiers: {0}'.format(' '.join(extra_mods))

    cumhitavg = 0.0
    cumwoundavg = 0.0
    for iteration in range(iterations):
        hits, wounds = do_one_attack(weapon, toughness, extra_mods)

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

    parser.add_argument('--iterations', type=int, help='The number of iterations to run', default=100000)

    # Attacking sim
    parser.add_argument('--toughness', type=int, help='The toughness of the monster', default=8)
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
    run_attack_sim(weapon, args.toughness, args.extra_mods, args.iterations)

    #for toughness in range(attack_data.toughness, 16, 1):
     #   attack_data.toughness = toughness
      #  attack_sim(args.iterations, attack_data)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
