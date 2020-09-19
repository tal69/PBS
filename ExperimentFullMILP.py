#-------------------------------------------------------------------------------
# Name:        ExperimentFullMILP
# Purpose:     Run the experiment with the full model (no replenishments)
#
# Author:      tal raviv,  talraviv@tau.ac.il
#
# Created:     23/08/2020, updated 18/9/2020
# Copyright:   (c) Tal Raviv 2020
# Licence:     Free but please let me know that you are using it
#-------------------------------------------------------------------------------

#import os
import random
import sys
import itertools
import subprocess
import pickle
import time
from PBSCom import *




file_export = ""  # set to "" if no script file is needed (the typical situation for the experiment)


""" consider getting this input from an external source """
alpha = 0; # C_max weight
beta = 1 # flowtime weight
gamma = 0.01 # movement weight
delta = 0.01 # queueing cost
time_limit = 900  # Time limit for cplex run (seconds)



# obtain command line paramteres
#  Lx, Ly, # reps, # loads, terminal1_X, terminal1_y, ..

if len(sys.argv) < 7:
    print("Usage: python %s Lx Ly reps_range target_load_num escorts_range IO_location_list" % sys.argv[0])
    exit(1)

Lx = int(sys.argv[1])
Ly = int(sys.argv[2])

reps_range = str2range(sys.argv[3])
load_num = int(sys.argv[4])
escorts_range = str2range(sys.argv[5])


ez = [int(a) for a in sys.argv[6:]]
O = []
for i in range(len(ez)//2):
    O.append((ez[i*2], ez[i*2+1]))

Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

f = open('res_full.csv','a')
f.write("date, Lx x Ly, #IOs, # Escorts, #Loads, IOs, Escorts, Target Loads, alpha, beta, gamma, makespan, flowtime, #load movements, obj, LB, CPU time, seed\n" )
f.close()

for escort_num in escorts_range:
    for rep in reps_range:
        random.seed(rep)
        f = open("pbs_full.dat","w")

        f.write('file_export = "%s";\n'%file_export)
        f.write('time_limit = %d;\n'% time_limit)
        f.write('alpha=%f;\n'%alpha)
        f.write('beta=%f;\n'%beta)
        f.write('gamma=%f;\n'%gamma)
        f.write('Lx=%d;\n'%Lx)
        f.write('Ly=%d;\n'%Ly)
        f.write('T=%d;\n'%((Lx+Ly)*3))  # just for now
        R,E = GeneretaeRandomInstance(rep, Locations, escort_num, load_num)
        f.write('E=%s;\n'%tuple_opl(E))
        f.write('R=%s;\n'%tuple_opl(R))
        f.write('O=%s;\n'%tuple_opl(O))
        f.close()

        try:
            subprocess.run(["oplrun", "pbs2.mod", "pbs_full.dat"], check=True)
        except:
            print("Could not solve the model")
            f = open('res_full.csv','a')
            f.write("%s, %dx%d, %d,%d,%d, %s, %s, %s, %1.3f, %1.3f, %1.3f, No solution, -,-,-,-,-, %d\n" %(time.ctime(),Lx,Ly, len(O), len(E), len(R), tuple_opl(O), tuple_opl(E), tuple_opl(R) , alpha,beta,gamma,rep))
            f.close()
        else:
            f = open('res_full.csv','a')
            f.write(",%d\n"% rep)
            f.close()
            # Create script file
            if file_export != "":

                f = open(file_export)
                s = f.readlines()
                moves = eval(s[-1])   # read moves in the currnet horizon
                f.close()
                pickle.dump( (Lx, Ly, O, E,R,moves),open("script_full_%d_%d_%d_%d_%d.p" % (Lx, Ly,escort_num, load_num,rep),"wb"))



