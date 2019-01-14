# KDMDice.py
#
# Monte Carlo sims for calculating optimal dice rolls
import argparse
import copy
import random
import sys


class Weapon(object):
    def __init__(self, speed, hit, strength):
        self.speed = speed
        self.hit = hit
        self.strength = strength


class AttackData(object):
    def __init__(self, toughness, weapon):
        self.toughness = toughness
        self.weapon = weapon
        self.savage = False
        self.cwaxe = False
        self.devastating = 0
        self.scrapsword = False
        self.scrapdagger = False
        self.screamingset = False
        self.earlyiron = False
        self.sharp = False
        self.hollow = False

    def is_wound(self, roll, strength):
        if roll == 1:
            return False
        if roll == 10:
            return True
        if self.sharp:
            strength += random.randint(1, 10)
        return roll + strength >= self.toughness

    @staticmethod
    def is_hit(roll, hit):
        return roll == 10 or (roll != 1 and (roll >= hit))

    @staticmethod
    def apply_hollow(roll):
        count = roll.count(10)
        while count > 0:
            new_roll = random.randint(1, 10)
            roll.append(new_roll)
            if new_roll != 10:
                count -= 1

    def run_attack_sim(self):
        # Snapshot weapon data to isolate any modifiers
        weapon = copy.deepcopy(self.weapon)
        hit_rolls = roll_n_dice(weapon.speed)
        if self.hollow:
            self.apply_hollow(hit_rolls)
        hits = 0.0
        wounds = 0.0
        auto_wound = False
        savage = self.savage
        if self.scrapsword and 10 in hit_rolls:
            weapon.strength += 4
        elif self.scrapdagger and 10 in hit_rolls:
            weapon.strength += 2

        if self.earlyiron and 1 in hit_rolls:
            return 0.0, 0.0

        for hit_roll in hit_rolls:
            if self.is_hit(hit_roll, weapon.hit):
                hits += 1.0
                if (self.cwaxe and hit_roll == 10) or auto_wound:
                    wounds += 1.0
                    continue
                wound_roll = random.randint(1, 10)
                if self.is_wound(wound_roll, weapon.strength):
                    wounds += 1.0
                    if self.devastating > 0:
                        wounds += self.devastating
                    if self.screamingset:
                        auto_wound = True
                if savage and wound_roll == 10:
                    wounds += 1.0
                    savage = False
        return hits, wounds


def roll_n_dice(n):
    roll = []
    for x in range(n):
        roll.append(random.randint(1, 10))
    return roll


def is_valid_roll(roll):
    return len(roll) == len(set(roll))


def roll_value(roll):
    if is_valid_roll(roll):
        return sum(roll)
    return 0


def gathering_sim(players, iterations):
    print 'Calculating gathering for {0} players at {1} iterations'.format(players, iterations)

    n_dice_avg = {}
    for iteration in range(iterations):
        for num_dice in range(2, 7):
            table_total = 0.0
            for player in range(players):
                table_total += roll_value(roll_n_dice(num_dice))

            if iteration == 0:
                n_dice_avg[num_dice] = table_total
            elif iteration == 1:
                n_dice_avg[num_dice] = (table_total + n_dice_avg[num_dice]) / 2
            elif iteration >= 2:
                # Cumulative moving average
                n_dice_avg[num_dice] = (n_dice_avg[num_dice] * iteration + table_total) / (iteration + 1)

        # print 'Table total for {0} dice is: {1}'.format(num_dice, table_total)

    for num_dice in range(2, 7):
        print '{0} dice cumulative average is {1}'.format(num_dice, n_dice_avg[num_dice])


def attack_sim(iterations, attack_data):
    print 'Calculating attack for {0}/{1}/{2} attack against {3} toughness at {4} iterations'.format(
        attack_data.weapon.speed, attack_data.weapon.hit, attack_data.weapon.strength, attack_data.toughness, iterations)

    cumhitavg = 0.0
    cumwoundavg = 0.0
    for iteration in range(iterations):
        hits, wounds = attack_data.run_attack_sim()

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

    print 'T{0} - Expected hits: {1:.2f}, wounds: {2:.2f}'.format(attack_data.toughness, cumhitavg, cumwoundavg)


def main():
    parser = argparse.ArgumentParser(prog="KDMDice",
                                     description='Calculate dice rolls for KD:M',
                                     add_help=True)
    parser.add_argument('mode', type=int, help='Which mode to run in. 1 is gathering sim. 2 is attack sim')

    # Gathering sim
    parser.add_argument('--players', type=int, help='The number of players rolling', default=None)
    parser.add_argument('--iterations', type=int, help='The number of iterations to determine percentages', default=None)

    # Attacking sim
    parser.add_argument('--toughness', type=int, help='The toughness of the monster', default=8)
    parser.add_argument('--speed', type=int, help='The speed of the attack', default=2)
    parser.add_argument('--hit', type=int, help='The hit value of the attack', default=7)
    parser.add_argument('--strength', type=int, help='The strength of the attack', default=3)
    parser.add_argument('--savage', type=int, help='Weapon has Savage', default=0)
    parser.add_argument('--cwaxe', type=int, help='Weapon is Counter-weight Axe', default=0)
    parser.add_argument('--devastating', type=int, help='Rank of weapon devastating', default=0)
    parser.add_argument('--scrapsword', type=int, help='Weapon is Scrap Sword', default=0)
    parser.add_argument('--scrapdagger', type=int, help='Weapon is Scrap Dagger', default=0)
    parser.add_argument('--screamingset', type=int, help='Activate bonus for Screaming Armor', default=0)
    parser.add_argument('--earlyiron', type=int, help='Weapon has Early Iron', default=0)
    parser.add_argument('--sharp', type=int, help='Weapon has Sharp', default=0)
    parser.add_argument('--hollow', type=int, help='On perfect hit make 1 additional attack roll', default=0)

    args = parser.parse_args()

    if args.mode == 1:
        gathering_sim(args.players, args.iterations)
    elif args.mode == 2:
        attack_data = AttackData(args.toughness, Weapon(args.speed, args.hit, args.strength))

        if args.savage:
            attack_data.savage = True
        if args.cwaxe:
            attack_data.cwaxe = True
        attack_data.devastating = args.devastating
        if args.scrapsword:
            attack_data.scrapsword = True
        if args.scrapdagger:
            attack_data.scrapdagger = True
        if args.screamingset:
            attack_data.screamingset = True
        if args.earlyiron:
            attack_data.earlyiron = True
        if args.sharp:
            attack_data.sharp = True
        if args.hollow:
            attack_data.hollow = True

        for toughness in range(attack_data.toughness, 16, 2):
            attack_data.toughness = toughness
            attack_sim(args.iterations, attack_data)
    else:
        print 'invalid mode'


if __name__ == "__main__":
    if not main():
        sys.exit(1)
