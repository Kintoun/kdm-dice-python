# RunIntoMaw.py
#
# Monte Carlo sims for calculating values and success rate
# for running into the maw in KDM
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


def maw_sim(iterations):
    print 'Calculating maw chances at {0} iterations'.format(iterations)

    n_dice_avg = {}
    n_dice_failures = {}
    for num_dice in range(2, 7):
        n_dice_failures[num_dice] = 0.0

    for iteration in range(iterations):
        for num_dice in range(2, 7):
            total = roll_value(roll_n_dice(num_dice))
            if total == 0.0:
                n_dice_failures[num_dice] += 1.0

            if iteration == 0:
                n_dice_avg[num_dice] = total
            elif iteration == 1:
                n_dice_avg[num_dice] = (total + n_dice_avg[num_dice]) / 2.0
            elif iteration >= 2:
                # Cumulative moving average
                n_dice_avg[num_dice] = (n_dice_avg[num_dice] * iteration + total) / (iteration + 1.0)

        # print 'Table total for {0} dice is: {1}'.format(num_dice, total)

    for num_dice in range(2, 7):
        print '{0} dice cumulative average is {1}, fail chance is {2:.1f}'.format(num_dice, n_dice_avg[num_dice], (n_dice_failures[num_dice] / iterations) * 100.0)


def main():
    parser = argparse.ArgumentParser(prog="RunIntoMaw",
                                     description='Calculate values and success chance for running into maw for KD:M',
                                     add_help=True)

    parser.add_argument('--iterations', type=int, help='The number of iterations to run',
                        default=100000)

    args = parser.parse_args()

    maw_sim(args.iterations)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
