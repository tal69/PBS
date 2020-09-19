#-------------------------------------------------------------------------------
# Name:        create_forbid_table

# Purpose:     Create a table with all the forbiden pair of esscort movement
#              to be imported by PBS_bm_mt
#              Conflicts
# Usage        Command line : python puzzle_block <Lx> <Ly>
#              But don't use the stand alone version
#
# Author:      Tal Raviv
#
# Created:     08-05-2018
# Copyright:   (c) Tal Raviv 2018
# Licence:     Free
# Checked and revised on Aug 17, 28, 31, 2019,
#
# 31-08-2019: The code here should be revised for elegancy and the format of the F table
# should be convereted to one used by the LM module
#-------------------------------------------------------------------------------


import time
import itertools
import pickle
import sys


def create_table(Lx , Ly):

    start_time = time.time()
    interval_time = time.time()

    Locations =  set(itertools.product(range(Lx), range(Ly)))
    F = set([])

    for (x10,y10) in Locations:

        for x11 in range(Lx):
            x1_min, x1_max = min(x10,x11), max(x10,x11)

            # same direction horizonatal movement
            for x20 in range(Lx):
                for x21 in range(Lx):
                    if min(x20,x21)<= x1_max and max(x20,x21) >= x1_max:
                        F.add((x10,y10,x11,y10,x20,y10,x21,y10))
                        F.add((x20,y10,x21,y10,x10,y10,x11,y10))


            # perpendicular  both directions
            for x2 in range(x1_min,x1_max+1):
                for y20 in range(Ly):
                    for y21 in range(Ly):
                        if min(y20,y21) <= y10 and  max(y20,y21)>= y10:
                            F.add((x10,y10,x11,y10,x2,y20,x2,y21))
                            F.add((x2,y20,x2,y21,x10,y10,x11,y10))


        for y11 in range(Ly):
            y1_min, y1_max = min(y10,y11), max(y10,y11)

            # same direction vertical movement
            for y20 in range(Ly):
                for y21 in range(Ly):
                    if min(y20,y21)<= y1_max and max(y20,y21) >= y1_max:
                        F.add((x10,y10,x10,y11,x10,y20,x10,y21))
                        F.add((x10,y20,x10,y21,x10,y10,x10,y11))



    print("Forbiden set creation time %1.3f seconds---" % (time.time() - start_time))
    return F




if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("usage: python", sys.argv[0],"<Lx> <Ly>")
        exit(1)

    (Lx, Ly) = (int(sys.argv[1]),int(sys.argv[2]))


    F = create_table(Lx,Ly)

    print("Number of entries in the forbiden set ",len(F))
    start_time = time.time()
    name = sys.argv[1]+"x"+sys.argv[2]+".p"
    pickle.dump( F, open( "F_"+name, "wb" ) )
    print("Saving time %1.3f seconds---" % (time.time() - start_time))
