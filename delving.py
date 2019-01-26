# delving.py
#
# Monte Carlo sims for calculating values and success rate
# for mining and delving in KDM
import argparse
import copy
import random
import sys


class MiningResults(object):
    def __init__(self):
        self.depth = 0.0
        self.hemo_disorder = 0.0
        self.random_disorder = 0.0
        self.scrap = 0.0
        self.iron = 0.0
        self.broken_pickaxe = 0.0
        self.crystal_skin = 0.0
        self.gear = 0.0
        self.dead = 0.0


def mineral_gathering(go_deeper, cumulative_results):
    roll = random.randint(1, 10)
    if roll <= 3:
        cumulative_results.hemo_disorder = 1.0
        return False
    if roll <= 5:
        cumulative_results.scrap += 1.0
        return False
    if roll <= 7:
        cumulative_results.iron += 1.0
        if random.randint(1, 10) >= 6:
            cumulative_results.broken_pickaxe = 1.0
        return False
    if roll >= 8:
        cumulative_results.scrap += 1.0
    return go_deeper


def worm_tunnels(sickle, go_deeper, cumulative_results):
    roll = random.randint(1, 10)
    if sickle:
        roll += 2

    if roll <= 3:
        cumulative_results.random_disorder = 1.0
        return False
    elif roll <= 7:
        return False
    # roll >= 8:
    else:
        if go_deeper:
            return True
        else:
            cumulative_results.iron += 1.0
            return False


def crystal_lake(whip, go_deeper, cumulative_results):
    roll = random.randint(1, 10)
    if whip:
        roll += 2

    if roll <= 2:
        cumulative_results.crystal_skin = 1.0
        return False
    elif roll <= 4:
        cumulative_results.random_disorder = 1.0
        return False
    elif roll <= 6:
        return False
    # roll >= 7:
    else:
        if go_deeper:
            return True
        cumulative_results.iron += 2.0
        return False


def lantern_city(almanac, cumulative_results):
    roll = random.randint(1, 10)
    if almanac:
        roll += 2

    if roll <= 4:
        cumulative_results.dead = 1.0
    elif roll <= 9:
        cumulative_results.iron += 4.0
        cumulative_results.scrap += 3.0
    # 10
    else:
        cumulative_results.gear = True


def mine(max_depth, sickle, whip, almanac, cumulative_results):
    if mineral_gathering(max_depth >= 1 or max_depth == 0, cumulative_results):
        cumulative_results.depth += 1.0
        if worm_tunnels(sickle, max_depth >= 2 or max_depth == 0, cumulative_results):
            cumulative_results.depth += 1.0
            if crystal_lake(whip, max_depth >= 3 or max_depth == 0, cumulative_results):
                lantern_city(almanac, cumulative_results)


def mining_sim(iterations, max_depth, sickle, whip, almanac):
    print 'Calculating mining at {0} iterations'.format(iterations)

    depth_count = 0.0
    hemo_disorder_chance_count = 0.0
    random_disorder_chance_count = 0.0
    scrap_count = 0.0
    iron_count = 0.0
    broken_pickaxe_chance_count = 0.0
    crystal_skin_chance_count = 0.0
    gear_chance_count = 0.0
    dead_chance_count = 0.0
    for iteration in range(iterations):
        cumulative_results = MiningResults()
        mine(max_depth, sickle, whip, almanac, cumulative_results)

        hemo_disorder_chance_count += cumulative_results.hemo_disorder
        random_disorder_chance_count += cumulative_results.random_disorder
        broken_pickaxe_chance_count += cumulative_results.broken_pickaxe
        crystal_skin_chance_count += cumulative_results.crystal_skin
        gear_chance_count += cumulative_results.gear
        dead_chance_count += cumulative_results.dead
        if iteration == 0:
            depth_count = cumulative_results.depth
            scrap_count = cumulative_results.scrap
            iron_count = cumulative_results.iron
        elif iteration == 1:
            # n_dice_avg[num_dice] = (table_total + n_dice_avg[num_dice]) / 2
            depth_count = (cumulative_results.depth + depth_count) / 2
            scrap_count = (cumulative_results.scrap + scrap_count) / 2
            iron_count = (cumulative_results.iron + iron_count) / 2
        elif iteration >= 2:
            # Cumulative moving average
            # n_dice_avg[num_dice] = (n_dice_avg[num_dice] * iteration + table_total) / (iteration + 1)
            depth_count = (depth_count * iteration + cumulative_results.depth) / (iteration + 1)
            scrap_count = (scrap_count * iteration + cumulative_results.scrap) / (iteration + 1)
            iron_count = (iron_count * iteration + cumulative_results.iron) / (iteration + 1)

    print 'Avg depth: {0:.2f}'.format(depth_count)
    # print 'Disorder counts: {0}'.format(disorder_chance_count)
    print 'Hemophobia disorder chance: {0}'.format(hemo_disorder_chance_count / iterations * 100.0)
    print 'Random disorder chance: {0}'.format(random_disorder_chance_count / iterations * 100.0)
    print 'Avg scraps: {0:.2f}'.format(scrap_count)
    print 'Avg iron: {0:.2f}'.format(iron_count)
    # print 'Broken pickaxe count: {0}'.format(broken_pickaxe_chance_count)
    print 'Broken pickaxe chance: {0}'.format(broken_pickaxe_chance_count / iterations * 100.0)
    # print 'Crystal skin count: {0}'.format(crystal_skin_chance_count)
    print 'Crystal skin chance: {0}'.format(crystal_skin_chance_count / iterations * 100.0)
    # print 'Blacksmith gear count: {0}'.format(gear_chance_count)
    print 'Blacksmith gear chance: {0}'.format(gear_chance_count / iterations * 100.0)
    # print 'Death count: {0}'.format(dead_chance_count)
    print 'Death chance: {0}'.format(dead_chance_count / iterations * 100.0)


def main():
    parser = argparse.ArgumentParser(prog="gathering",
                                     description='Calculate values and success chance for herb gathering in KD:M',
                                     add_help=True)

    parser.add_argument('--iterations', type=int, help='The number of iterations to run', default=1000000)
    parser.add_argument('--max_depth', type=int, help='Max depth to delve.', default=0)

    args = parser.parse_args()
    # print '\nSim with sickle + whip + almanac'
    # mining_sim(args.iterations, args.max_depth, True, True, True)
    # print '\nSim with sickle + whip'
    # mining_sim(args.iterations, args.max_depth, True, True, False)
    # print '\nSim with sickle'
    # mining_sim(args.iterations, args.max_depth, True, False, False)
    # print '\nSim with whip'
    # mining_sim(args.iterations, args.max_depth, False, True, False)
    # print '\nSim with nothing'
    # mining_sim(args.iterations, args.max_depth, False, False, False)
    print '\nSim with Sickle and Whip, stopping at Crystal Lake'
    mining_sim(args.iterations, 2, True, True, False)
    print '\nSim with Sickle, stopping at Crystal Lake'
    mining_sim(args.iterations, 2, True, False, False)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
