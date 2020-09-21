#-------------------------------------------------------------------------------
# Name:        PBS_MDPHeuristic_lm.py
# Purpose:     load data, generate instance and apply the M-DP heurstic  for the LM case
#              PBSk|sim,lm,mIO| *
#              The objective function * determined by the DP table
#              The idea is similar to the DP heuristic but here we apply several
#              actions in paralel by solving a set covering problem
#
# Author:      Tal Raviv talraviv@au.ac.il
#
# Created:     25-06-2020
# Updated      10-09-2020  (add shortest path shortcut)
# Copyright:   (c) TAL 2020
# Licence:     Free to use but please contact me
#-------------------------------------------------------------------------------


import sys
import pickle
from PBSCom import *
import itertools
import random
import time
import subprocess


scripts_path = "phase1LM"  # folder for the output script files
reps = 20 # number of replications



#  Main heuristic routine
# S - DP table dict
# I - loaction of the retrievd load  (2-tuple)
# E  locations of the escorts (list of tuples)
# Lx, Ly - dimension of the PBS unit
# Terminals  locations of the IOs (list of tuples)
def MDPHueristicLM(S, I, E, Lx , Ly, Terminals,k, chat=True ):

# TODO
# 1) Use several DP tables for various k'
# 2) Eliminate sets with non-positive values (but handle the indices of the sets correctly)
    t = 0

    moves = []
    Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

    while True:


        if chat:
            Ix, Iy = I
            print("Period ",t," - ",(Ix,Iy),E)

            for y in range(Ly-1,-1,-1):
                for x in range(Lx):

                    if (Ix,Iy) == (x,y):
                        print("$",end="")
                    elif  (x,y) in E:
                        print(".",end="")
                    elif (x,y) in Terminals:
                        print("T",end="")
                    else:
                        print("*",end="")
                print("")
            print("")

            t+= 1

        ez = ShortestPath(I,E,Terminals)
        if ez:
            if chat:
                print("Finish by free shortest path")
            return moves+[ [a] for a in ez]

        # Constructs sets
        Sets = {}
        SetsLookup = {}
        counter = 0
        min_val = 9999999
        for Et in itertools.combinations(E, k):
            EE = sorted(Et)

            p = listTuple2Int([I]+EE, Lx, Ly)
            p_val, next_p = S[p]
            min_val =  min(min_val,p_val)
            next_EE = int2ListTuple(next_p,  Lx, Ly)[1:]
            # BUG HERE - eliminate movement of an escort into an escort
            Elements = frozenset(EE) ^ frozenset(next_EE)
            if not Elements in Sets or p_val < Sets[Elements][1]:
                Sets[Elements] = ([(next_EE[i], EE[i]) for i in range(k) if EE[i] != next_EE[i] and not next_EE[i] in E],p_val)
                SetsLookup[counter] = Elements
                counter += 1

        # Build input for SetPacking model
        f = open("SetPackingTmp.dat","w")
        f.write("num_sets = %d;\n"% len(Sets))
        f.write("L = %s;\n"% tuple_opl(Locations))
        f.write("v = [")
        for s,v in Sets.items():
            val = len(s)-v[1]+min_val
            #if (val>0):
            f.write("%d "%val)
        f.write("];\n")
        f.write("E = [")
        for s,v in Sets.items():
            val = len(s)-v[1]+min_val
            #if (val>0):
            f.write("%s "%tuple_opl(s))
        f.write("];\n")

        f.close()

        try:
            subprocess.run(["oplrun", "SetPacking.mod", "SetPackingTmp.dat"], check=False)
        except:
            print("Panic: Could not solve the model")
            exit(1)

        SetPackingSol =eval(open("SetPacking.txt").read())

        curr_move = []
        for i in SetPackingSol:
            curr_move += list(Sets[SetsLookup[i]][0])

        moves.append(curr_move)

        # Update E  - think how to make it more pythonic
        Eset = set(E)
        for m in curr_move:
            Eset.add(m[0])
            Eset.remove(m[1])
            if I == m[0]:
                I= m[1]

        E = sorted(list(Eset))

    return moves





if __name__ == '__main__':


    if len(sys.argv) < 4:
        print("usage: python", sys.argv[0],"<setting_file of the base problem> <range actual esscorts>  <range seed>")

        exit(1)


    if sys.argv[1][-3:].upper()== ".PY":
        sys.argv[1] = sys.argv[1][:-3]

    name = sys.argv[1]

    exec("from "+name+" import *")
    k_range = str2range(sys.argv[2])
    if k-1 in k_range:
        print('Panic: cannot solve using k=%d instances in the range %d' % (k,sys.argv[2]))
        exit(1)

    rep_range = str2range(sys.argv[3])

    Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

    S = pickle.load( open( "LM_"+sys.argv[1]+".p", "rb" ) )
    f = open("res_mdph_lm.csv", "a")
    f.write("Date, name, Model, Lx x Ly, seed, IOs, #escorts, k', Load, Escorts, ret. time, #moves, cpu time\n")
    f.close()

    for K in k_range:
        for i in rep_range:
            I, E = GeneretaeRandomInstance(i, Locations, K)

            I = I[0]  #  Here we assume a single retrival only now.

            startTime = time.time()
            moves = MDPHueristicLM(S, I,E, Lx, Ly, Terminals, k, True)


            f = open("res_mdph_lm.csv", "a")
            f.write("%s, %s, LM, %dx%d, %d, %s,%d,  %s, %s, %s, %d, %d, %1.3f\n" %(time.ctime(),name,Lx,Ly,  i, str(Terminals).replace(",",""), K, k,  str(I).replace(",",""),  tuple_opl( E), len(moves), sum([ len(a) for a in moves]) ,time.time()-startTime))
            f.close()

            # Uncomment to create animation scripts
            f = open(scripts_path+"/MDPH_LM_%d_%d_%d_%d_%d.p" % (Lx, Ly,len(E), k,i),"wb")
            pickle.dump( (Lx, Ly, Terminals, E,[I],moves),f)
            f.close()