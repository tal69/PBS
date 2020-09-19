#-------------------------------------------------------------------------------
# Name:        simulate_ret.py
# Purpose:     Simulate sequential retrival of many itemes one after another
#
# Author:      Tal Raviv talraviv@tauex.tau.ac.il
#
# Created:     28-08-2019
# Copyright:   (c) TAL 2018
# Licence:     Free to use but please contact me
#-------------------------------------------------------------------------------



import sys
import pickle
import PBS_bm_mt as pz
import random
import statistics
import math


def rand_load_location(E, Lx, Ly):
    while True:
            I = (random.randrange(Lx), random.randrange(Ly))
            if not I in E:
                break
    return I

if __name__ == '__main__':

    if len(sys.argv) < 5:
        print("usage: python", sys.argv[0],"<model_file> <LM|BM> <replications> <warm_up>")
        exit(1)

    # cut the py extention for the import operation
    if sys.argv[1][-3:].upper()== ".PY":
        sys.argv[1] = sys.argv[1][:-3]

    exec("from "+sys.argv[1]+" import *")

    ModelType = sys.argv[2].upper()
    if not ModelType in ["LM", "BM"]:
        print('Panic: model type (2nd argument) should be either LM or BM. Cannot be %s ' % sys.argv[2])
        exit(1)

    replications, warm_up = int(sys.argv[3]), int(sys.argv[4])

    S = pickle.load( open( ModelType+"_"+sys.argv[1]+".p", "rb" ) )

    observations = []

    E = [(i,0) for i in range(k) ]  # start with the escorts at the left side of the lower wall
    # L.sort() non need

    lNewLoad = True
    count = 0
    total_ret_time = 0
    print("Starting...")

    while True:

        if lNewLoad:
            I = rand_load_location(E,Lx,Ly)
            p = pz.listTuple2Int([I]+E, Lx, Ly)
            count += 1

            if count > warm_up:
                total_ret_time += S[p][0]
                observations.append(S[p][0])
            if count >= replications:
                break


                print("panic3")


            lNewLoad = False
        if not p in S:
            print("Panic")

        if S[p][1]=="Sink":
            lNewLoad = True
        else:

            p = pz.sortIntState(S[p][1],Lx, Ly)


    mean_ret = statistics.mean(observations)
    std_ret = statistics.stdev(observations)
    N = len(observations)
    CI99 = 2.576 * std_ret/ math.sqrt(N)
    print("Average retrival time in %d trials is %1.3f, STD %1.3f  C.I 99%% (%1.3f, %1.3f) " % (N, mean_ret, std_ret, mean_ret-CI99, mean_ret+CI99))