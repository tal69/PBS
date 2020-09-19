#-------------------------------------------------------------------------------
# Name:        create_forbid_table

# Purpose:     Create a table with all the forbiden pair of esscort movement
#              to be used by Puzzle_load_mt
#              Better used as a package to directly create the table since it
#              created so fast
# Usage        Don't. This is imported by puzzle_load_mt
#
# Author:      Tal Raviv
#
# Created:     31-08-2019
# Copyright:   (c) Tal Raviv 2019
# Licence:     Free
#-------------------------------------------------------------------------------


import time
import itertools
import pickle
#import sys

#import math

# Create table entry for four tuples
def te(a,b,c,d):
    return(frozenset([frozenset([tuple(a),tuple(b)]), frozenset([tuple(c),tuple(d)])]))

def create_forbid_table(L):

    start_time = time.time()
    interval_time = time.time()

    Locations =  set(itertools.product(range(L[0]), range(L[1])))
    F = set([])

    Orig1 = [-1,-1]
    Dest1 = [-1,-1]
    Dest = [-1,-1]
    for O_ez in Locations:
        Orig = list(O_ez)
        for d in range(2):
            for i in range(2):
                Dest[d] = Orig[d] + i

                # Parallel
                Dest[1-d] = Orig[1-d]

                Orig1[1-d] = Orig[1-d]
                Dest1[1-d] = Orig[1-d]

                # Swap places  1->2 and 2->1   or 1->1 and 2->1
                Orig1[d], Dest1[d] = Dest[d], Orig[d]
                F.add(te(Orig,Dest, Orig1,Dest1))

                # 1->2 and 2->3  or 1->1 and 1->2 (redundent)
                if Dest[d] < L[d]-1:
                    Orig1[d], Dest1[d] =  Dest[d], Dest[d]+1
                    F.add(te(Orig,Dest, Orig1,Dest1))

                # 1->2 and 0->1  or 1->1 and 0->1
                if Dest[d] > 0:
                    Orig1[d], Dest1[d] =  Orig[d]-1, Orig[d]
                    F.add(te(Orig,Dest, Orig1,Dest1))



            # Perpendicular

            if Orig[1-d] > 0:
                Orig1[1-d] = Orig[1-d] - 1
                Dest1[1-d] = Orig[1-d]

                Orig1[d], Dest1[d] = Orig[d], Orig[d]
                F.add(te(Orig,Dest, Orig1,Dest1))
                Orig1[d], Dest1[d] = Dest[d], Dest[d]
                F.add(te(Orig,Dest, Orig1,Dest1))


            if Orig[1-d] < L[1-d]-1:
                Orig1[1-d] = Orig[1-d]
                Dest1[1-d] = Orig[1-d] +1

                Orig1[d], Dest1[d] = Orig[d], Orig[d]
                F.add(te(Orig,Dest, Orig1,Dest1))
                Orig1[d], Dest1[d] = Dest[d], Dest[d]
                F.add(te(Orig,Dest, Orig1,Dest1))
    return F




"""
def main():
    if len(sys.argv) < 3:
        print("usage: python", sys.argv[0],"<Lx> <Ly>")
        exit(1)

    (Lx, Ly) = (int(sys.argv[1]),int(sys.argv[2]))


    name = sys.argv[1]+"x"+sys.argv[2]+".p"

    start_time = time.time()

    F = create_forbid_table((Lx,Ly))

    print("Forbiden set creation time %1.3f seconds---" % (time.time() - start_time))
    print("Number of entries in the forbiden set ",len(F))
    start_time = time.time()
    pickle.dump( F, open( "FLM_"+name, "wb" ) )
    print("Saving time %1.3f seconds---" % (time.time() - start_time))


if __name__ == '__main__':
    # define globals
    main()
"""