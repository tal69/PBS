#-------------------------------------------------------------------------------
# Name:        PBS_DPHeuristic_lm.py
# Purpose:     load data, generate instance and apply the DP heurstic  for the LM case
#              PBSk|sim,lm,mIO| *
#              The objective function * determined by the DP table
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

scripts_path = "phase1LM"  # folder for the output script files
reps = 20 # number of replications



#  Main heuristic routine
# S - DP table dict
# I - loaction of the retrievd load  (2-tuple)
# E  locations of the escorts (list of tuples)
# Lx, Ly - dimension of the PBS unit
# Terminals  locations of the IOs (list of tuples)
def DOHueristicLM(S, I, E, Lx , Ly, Terminals,k, chat=True ):
    t = 0

    moves = []

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

        min_val = 9999999



        ez = ShortestPath(I,E,Terminals)
        if ez:
            print("*****  Finish with shortest path shortcut ******")
            return moves+[ [a] for a in ez]

        for Et in itertools.combinations(E, k):
            EE = sorted(list(Et))
            p = listTuple2Int([I]+EE, Lx, Ly)
            if S[p][0]< min_val:
                min_val = S[p][0]
                best_EE = EE
                #if min_val+1 == min([ L1(I, Ter) for Ter in Terminals]):  # DONT SURE IT HELPS
                #    break



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
            if best_EE[i] != new_EE[i]:
                curr_move.append((new_EE[i], best_EE[i]))   # Recall that the load movement is opposite to the escort movement
        moves.append(curr_move)



        # Update E  - think how to make in more pythonic
        Eset = set(E)
        for i in range(len(best_EE)):
            if not new_EE[i] in E:
                Eset.remove(best_EE[i])
            Eset.add(new_EE[i])

        #E = list((set(E) - set(best_EE)) | (set(new_EE)))  # fine new E
        E = list(Eset)



        E.sort()

    return moves





if __name__ == '__main__':


    if len(sys.argv) < 3:
        print("usage: python", sys.argv[0],"<setting_file of the base problen> <max number of actual esscorts>")

        exit(1)


    if sys.argv[1][-3:].upper()== ".PY":
        sys.argv[1] = sys.argv[1][:-3]

    name = sys.argv[1]

    exec("from "+name+" import *")
    max_K = int(sys.argv[2])

    Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

    S = pickle.load( open( "LM_"+sys.argv[1]+".p", "rb" ) )
    f = open("res_dph_lm.csv", "a")
    f.write("Date, name, Model, Lx x Ly, seed, IOs, #escorts, k', Load, Escorts, ret. time, cpu time\n")
    f.close()

    #for K in [16]:
    for K in range(k,min(max_K+1, Lx*Ly-k+1)):
        for i in range(reps):
        #for i in [1]:
            I, E = GeneretaeRandomInstance(i, Locations, K)
            I = I[0]  #  Here we assume a single retrival only now.

            startTime = time.time()
            moves = DOHueristicLM(S, I,E, Lx, Ly, Terminals, k, False)

            f = open("res_dph_lm.csv", "a")
            f.write("%s, %s, LM, %dx%d, %d, %s,%d,  %s, %s, %s, %d, %1.3f\n" %(time.ctime(),name,Lx,Ly,  i, str(Terminals).replace(",",""), K, k,  str(I).replace(",",""),  str(E).replace(",",""), len(moves), time.time()-startTime))
            f.close()

            # Uncomment to create animation scripts
            f = open(scripts_path+"/DPH_LM_%d_%d_%d_%d_%d.p" % (Lx, Ly,len(E), k,i),"wb")
            pickle.dump( (Lx, Ly, Terminals, E,[I],moves),f)
            f.close()