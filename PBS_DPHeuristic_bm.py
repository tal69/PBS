#-------------------------------------------------------------------------------
# Name:        PBS_DPHeuristic_bm.py
# Purpose:     load data, generate instance and apply the DP heurstic  for the LM case
#              PBSk|sim,lm,mIO| *
#              The objective function * determined by the DP table
#              Block movement version
#
# Author:      Tal Raviv talraviv@au.ac.il
#
# Created:     25-06-2020
# Copyright:   (c) TAL 2020
# Licence:     Free to use but please contact me
#-------------------------------------------------------------------------------


import sys
import pickle
from PBSCom import *
import itertools
import random
import time
import copy

scripts_path = "phase1BM"
reps = 20  # number of replications



# assume two 2-tuples as input return a directional vector
def direction(a,b):

    if a[0]<b[0]:
        return ((1,0))
    elif a[0]>b[0]:
        return ((-1,0))
    elif a[1]<b[1]:
        return ((0,1))
    elif a[1]>b[1]:
        return ((0,-1))
    else:
        return ((0,0))


# Prints the optimal path from state S
#  This is improted by  the path_print_dp.py program
def DOHueristicBM(S, I, E, Lx , Ly, Terminals,k, chat=True ):
    t = 0

    E_local = copy.copy(E)

    moves = []

    while True:


        if chat:
            Ix, Iy = I
            print("Period ",t," - ",(Ix,Iy),E_local)

            for y in range(Ly-1,-1,-1):
                for x in range(Lx):

                    if (Ix,Iy) == (x,y):
                        print("$",end="")
                    elif  (x,y) in E_local:
                        print(".",end="")
                    elif (x,y) in Terminals:
                        print("T",end="")
                    else:
                        print("*",end="")
                print("")
            print("")


        ez = ShortestPath(I,E_local,Terminals)
        if ez:
            print("*****  Finish with shortest path shortcut ******")
            return moves+[ [a] for a in ez]

        min_val = 9999999

        for Et in itertools.combinations(E_local, k):
            EE = sorted(list(Et))
            p = listTuple2Int([I]+EE, Lx, Ly)
            if p == 186770:
                print("bug here")

            if S[p][0]< min_val:
                min_val = S[p][0]
                best_EE = EE




        best_EE.sort()
        p = S[listTuple2Int([I]+best_EE, Lx,Ly)][1]
        t += 1

        if p == "Sink":
            break

        L = int2ListTuple(p,  Lx, Ly)
        I = L[0]
        new_EE = L[1:]

        curr_move = []
        for i in range(len(best_EE)):
            curr_loc = best_EE[i]
            d = direction(best_EE[i], new_EE[i])
            while curr_loc != new_EE[i]:
                next_loc = (curr_loc[0]+d[0], curr_loc[1]+d[1])
                if not next_loc in E_local:
                    curr_move.append((next_loc, curr_loc))   # Recall that the load movements are opposite to the escort movement
                    E_local.remove(curr_loc)
                    E_local.append(next_loc)
                curr_loc = next_loc

        moves.append(curr_move)
        E_local.sort()
    return moves



if __name__ == '__main__':



    if len(sys.argv) < 4:
        print("usage: python", sys.argv[0],"<setting_file of the base problem> <range actual esscorts>  <range seed>")
        exit(1)

    if sys.argv[1][-3:].upper()== ".PY":
        sys.argv[1] = sys.argv[1][:-3]
    name =sys.argv[1]

    exec("from "+name+" import *")
    k_range = str2range(sys.argv[2])
    if k-1 in k_range:
        print('Panic: cannot solve using k=%d instances in the range %d' % (k,sys.argv[2]))
        exit(1)

    rep_range = str2range(sys.argv[3])

    Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))
    S = pickle.load( open( "BM_"+sys.argv[1]+".p", "rb" ) )
    f = open("res_dph_bm.csv", "a")
    f.write("Date, Name, Model, Lx x Ly, seed, IOs, #escorts, k', Load, Escorts, ret. time, #moves, cpu time\n")
    f.close()



    for K in k_range:
        for i in rep_range:
            I, E = GeneretaeRandomInstance(i, Locations, K)

            I = I[0]  #  Here we assume a single retrival only now.

            startTime = time.time()
            moves = DOHueristicBM(S, I,E, Lx, Ly, Terminals, k, False)

            f = open("res_dph_bm.csv", "a")
            f.write("%s, %s, BM, %dx%d, %d, %s,%d,  %s, %s, %s, %d, %d, %1.3f\n" %(time.ctime(),name, Lx,Ly,  i, str(Terminals).replace(",",""), K, k,  str(I).replace(",",""),  tuple_opl(E), len(moves), sum([ len(a) for a in moves]),time.time()-startTime))
            f.close()


            # Comment to skip creating animation scripts
            f = open(scripts_path+"/DPH_BM_%d_%d_%d_%d_%d.p" % (Lx, Ly,len(E), k,i),"wb")
            pickle.dump( (Lx, Ly, Terminals, E,[I],moves),f)
            f.close()
