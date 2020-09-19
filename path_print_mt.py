#-------------------------------------------------------------------------------
# Name:        path_print_mt
# Purpose:     load data and print a path from a particular state
#              adapted for the block movement technology
#               handles multi-depot and reads setting file
#
# Author:      Tal Raviv talraviv@tauex.tau.ac.il
#
# Created:     19-04-2018
# Copyright:   (c) TAL 2018
# Licence:     Free to use but please contact me
#-------------------------------------------------------------------------------


import sys
import pickle
from PBSCom import *

# Prints the optimal path from state S
#  This is improted by  the path_print_dp.py program
def path_print(S, n, Lx , Ly, Terminals):
    t = 0
    while True:
        ez = int2ListTuple(n, Lx, Ly)
        Ix, Iy = ez[0]
        E = set(ez[1:])

        print("Period ",t," - ",(Ix,Iy),E,n)

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


        sn = sortIntState(n,Lx,Ly)
        if not sn in S:  # just foe debugging remove later
            print(sn, int2ListTuple(sn, Lx, Ly), int2ListTuple(n, Lx, Ly))
            exit(-1)

        n = S[sortIntState(n,Lx,Ly)][1]
        t += 1

        if n == "Sink":
            break
        #else:
        #    print(n, int2ListTuple(n,Lx,Ly), sortIntState(n,Lx,Ly), int2ListTuple(sortIntState(n,Lx,Ly),Lx,Ly))



if __name__ == '__main__':
    if len(sys.argv) < 6:
        print("usage: python", sys.argv[0],"<setting_file> <Ix> <Iy> <E1x> <E1y> , ...")
        print("Ix, Iy - initial locations of retrieved item")
        print("E1x, E1y, ... - initial locations of escorts")
        print("Attention: all the coordinate locations are starting from 0 and not form 1")
        exit(1)

    exec("from "+sys.argv[1]+" import *")

    (Ix, Iy) = tuple([int(sys.argv[i]) for i in range(2,4)])

    k = len(sys.argv) - 4
    if k % 2 == 1:
        print("Panic: must have even number of escorts coordinate")
        exit(1)

    k = k // 2

    L = [(int(sys.argv[2*i+4]), int(sys.argv[2*i+5])) for i in range(k) ]
    L.sort()

    L.insert(0,(Ix,Iy))


    name = sys.argv[1]+".p"

    print(sys.argv[1])
    if (not Ix in range(Lx)) or (not Iy in range(Ly)):
        print("Panic: initial item location is out of range (recall that the locations are indexed from 0")
        exit(1)


    S = pickle.load( open( "BM_"+name, "rb" ) )

    p = listTuple2Int(L, Lx, Ly)

    path_print(S, p, Lx, Ly, Terminals)




