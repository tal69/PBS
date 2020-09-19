#-------------------------------------------------------------------------------
# Name:        Rolling
# Purpose:     Apply the rolling horizon algorithm
#
# Author:      tal raviv,  talraviv@tau.ac.il
#
# Created:     21/08/2020
# Copyright:   (c) tal raviv 2020
# Licence:     Free but please let me know that you are using it
#-------------------------------------------------------------------------------

#import os
import random
import sys
import itertools
import subprocess
import pickle
import time

rnd_seed = 0

"""
   [(1,1),(2,3)] -> {<1 1>  <2 3>}
"""
def tuple_opl(L):

    s = "{"

    for t in L:
        s +=  "<"+str(t[0])+" "+str(t[1])+"> "

    return s +"}"



file_export = "out.txt"


""" consider getting this input from an external source """
alpha = 0; # C_max weight
beta = 1 # flowtime weight
gamma = 0.01 # movement weight
delta = 0.01 # queueing cost
incentive = 0.05  # incentive for reaching lonely loads



# obtain command line paramteres
#  Lx, Ly, # escorts, # loads, horizon length (T), rolling period (TT), terminal1_X, terminal1_y, ..

Lx = int(sys.argv[1])
Ly = int(sys.argv[2])

#escort_num = int(sys.argv[3])
reps = int(sys.argv[3])
load_num = int(sys.argv[4])

T = int(sys.argv[5])
TT = int(sys.argv[6])

ez = [int(a) for a in sys.argv[7:]]
O = []
for i in range(len(ez)//2):
    O.append((ez[i*2], ez[i*2+1]))



for i in range(10):
    for rep in range(reps):

        random.seed(rep)
        escort_num = int((i/20)*Lx*Ly+1)


        f = open("pbscom.dat","w")

        f.write('file_export = "%s";\n'% file_export)
        f.write('alpha=%f;\n'%alpha)
        f.write('beta=%f;\n'%beta)
        f.write('gamma=%f;\n'%gamma)
        f.write('delta=%f;\n'%delta)
        f.write('incentive=%f;\n'%incentive)

        f.write('Lx=%d;\n'%Lx)
        f.write('Ly=%d;\n'%Ly)

        f.write('T=%d;\n'%T)
        f.write('TT=%d;\n'%TT)

        f.write('O=%s;\n'%tuple_opl(O))
        f.write('I ={};\n')
        f.close()



        Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))
        ez = random.sample(Locations,escort_num+load_num)

        E = ez[:escort_num]
        R = ez[escort_num:]

        f = open("InitLoc.dat","w")
        f.write('E=%s;\n'%tuple_opl(E))
        f.write('R=%s;\n'%tuple_opl(R))
        f.write('RT = [];\n')
        f.write('ofset_time = 0;\n')
        f.close()

        moves = []

        start_time = time.time()


        while True: # will exit with breadk


            #os.remove("export.txt")  # We delete this file to make sure that an error will occur if Cplex fails
            subprocess.run(["oplrun", "pbs4.mod", "pbscom.dat", "InitLoc.dat"], check=True)

            f = open("out.txt")
            s = f.readlines()
            new_moves = eval(s[-1])   # read moves in the currnet horizon
            f.close()

            for a in new_moves:
                if a:  # not empty
                    moves.append(a)

            if len(new_moves[-1]) == 0:  # empty moves at the end
                break


        flow_time = 0
        c_max = 0
        num_of_moves = 0
        for t in range(len(moves)):
            for m in moves[t]:
                if m[1] == (None, None):
                    c_max = t-1
                    flow_time += (t-1)
                else:
                    num_of_moves += 1


        f = open("res_rolling_%dx%d_%d_%d.csv"%(Lx, Ly, T,TT),"a")
        f.write("%s, %dx%d, %d,%d,%d, %s, %s, %s, %1.3f, %1.3f, %1.3f, %d, %d, %d, %d, %1.3f\n" %
        (time.ctime(),Lx,Ly,len(O), len(E), len(R).tuple_opl(O), tuple_opl(E), tuple_opl(R) ,alpha, beta, gamma, rep, c_max, flow_time, num_of_moves, c_time.time()-start_time))
        f.close()

        # Create script file
        pickle.dump( (Lx, Ly, O, E,R,moves),open("script_%d_%d_%d_%d_%d.p" % (Lx, Ly,rep,len(E), len(R)),"wb"))





