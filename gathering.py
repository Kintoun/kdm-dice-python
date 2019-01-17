# Gathering.py
#
# Monte Carlo sims for calculating values and success rate
# for gathering herbs in KDM
import argparse
import copy
import random
import sys


def roll_n_dice(n):
    roll = []
    for _ in range(n):
        roll.append(random.randint(1, 10))
    return roll


def is_valid_roll(roll):
    return len(roll) == len(set(roll))


def roll_value(roll):
    if is_valid_roll(roll):
        return sum(roll)
    return 0.0


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


def main():
    parser = argparse.ArgumentParser(prog="gathering",
                                     description='Calculate values and success chance for herb gathering in KD:M',
                                     add_help=True)

    parser.add_argument('--players', type=int, help='The number of players to sim', default=4)
    parser.add_argument('--iterations', type=int, help='The number of iterations to run', default=100000)

    args = parser.parse_args()

    gathering_sim(args.players, args.iterations)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
