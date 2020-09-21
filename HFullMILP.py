#-------------------------------------------------------------------------------
# Name:        HFullMILP
# Purpose:     Run the experiment with the full model (no replenishments)
#              Use heuristic solution as upper bound
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
import PBS_DPHeuristic_lm
import PBS_DPHeuristic_bm


scripts_path = "scripts_full_milp"


file_export = "script_export"  # set to "" if no script file is needed (the typical situation for the experiment)
#file_export = ""

""" consider getting this input from an external source """
alpha = 0; # C_max weight
beta = 1 # flowtime weight
gamma = 0.01 # movement weight
delta = 0.01 # queueing cost
time_limit = 300  # Time limit for cplex run (seconds)


# obtain command line paramteres

if len(sys.argv) < 9:
    print("Usage: python %s Lx Ly reps_range target_load_num escorts_range DPTablesFile MoveMethod(LM|BM) IO_location_list" % sys.argv[0])
    exit(1)

Lx = int(sys.argv[1])
Ly = int(sys.argv[2])

reps_range = str2range(sys.argv[3])
load_num = int(sys.argv[4])
escorts_range = str2range(sys.argv[5])
DPTablesFile =  sys.argv[6]
MoveMethod = sys.argv[7].upper()

if not MoveMethod in ["LM", "BM"]:
    print("Panice: MoveMethod (6th argument) must be either LM or BM")


# Get list of DP table files
f = open(DPTablesFile,"r")
DPFiles = f.readlines()
f.close()
DPFiles =[s[:-1] for s in DPFiles]
Max_k_prime = len(DPFiles)
DPTableLoaded = False

ez = [int(a) for a in sys.argv[8:]]
O = []
for i in range(len(ez)//2):
    O.append((ez[i*2], ez[i*2+1]))

Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

f = open('res_Hfull.csv','a')
f.write("date, Regime, Lx x Ly, seed, #IOs, # Escorts, #Loads, IOs, Escorts, Target Loads, alpha, beta, gamma, k', Makespan (Hueristic), #load movments hueristic,  obj heurustuic, CPU time h, Makespan exact, #load movements, obj, LB, CPU time\n" )
f.close()

for escort_num in escorts_range:

    if escort_num <= Max_k_prime:
        print("Loading DP file %s..."%DPFiles[escort_num-1], flush=True)
        S = pickle.load( open( DPFiles[escort_num-1], "rb" ) )
        print("Done", flush=True)
    elif not DPTableLoaded and Max_k_prime > 0:
        S = pickle.load( open( DPFiles[-1], "rb" ) )
    DPTableLoaded = True

    for rep in reps_range:
        random.seed(rep)
        R,E = GeneretaeRandomInstance(rep, Locations, escort_num, load_num)

        StartTime = time.time()

        if Max_k_prime > 0:
            if MoveMethod == "LM":
                moves = PBS_DPHeuristic_lm.DOHueristicLM(S,R[0],E, Lx,Ly, O,min(Max_k_prime, escort_num), False)
            else: # BM
                moves = PBS_DPHeuristic_bm.DOHueristicBM(S,R[0],E, Lx,Ly, O,min(Max_k_prime, escort_num), False)

            T = len(moves)
            load_movements_h = sum([ len(a) for a in moves])
            obj_h = beta*T+load_movements_h*gamma

            print("Used heuristic with k'=%d to find T=%d"%(min(Max_k_prime, escort_num), T), flush=True)
        else:
            T = (Lx+Ly)*3   # a wild guess


        f = open('res_Hfull.csv','a')
        f.write("%s, %s, %dx%d, %d, %d,%d,%d, %s, %s, %s, %1.3f, %1.3f, %1.3f, %d, %d, %d, %1.3f, %1.3f, " %\
            (time.ctime(),MoveMethod, Lx,Ly, rep, len(O), len(E), len(R), tuple_opl(O), tuple_opl(E), tuple_opl(R) ,\
             alpha,beta,gamma, min(Max_k_prime, escort_num), T, load_movements_h, obj_h, time.time() - StartTime ))
        f.close()


        if escort_num > min(Max_k_prime, escort_num):

            f = open("pbs_full.dat","w")
            f.write('file_export = "%s";\n'%file_export)
            f.write('MoveMethod = "%s";\n'%MoveMethod)
            f.write('time_limit = %d;\n'% time_limit)
            f.write('alpha=%f;\n'%alpha)
            f.write('beta=%f;\n'%beta)
            f.write('gamma=%f;\n'%gamma)
            f.write('Lx=%d;\n'%Lx)
            f.write('Ly=%d;\n'%Ly)
            f.write('T=%d;\n'%T)
            f.write('E=%s;\n'%tuple_opl(E))
            f.write('R=%s;\n'%tuple_opl(R))
            f.write('O=%s;\n'%tuple_opl(O))
            f.close()



            try:
                subprocess.run(["oplrun", "pbs2a.mod", "pbs_full.dat"], check=True)
            except:
                print("Could not solve the model")
                f = open('res_Hfull.csv','a')
                f.write("No solution, -,-,-, %1.3f\n" %(time.time()-StartTime))
                f.close()
                continue  # skip to next instance without creating a script file
            else:
                exec(open("out_pbs2a.txt").read())  # Read the variables z,FlowTime, NumberOfMovements, obj, lb. Yes, I know this is ugly.
                f = open('res_Hfull.csv','a')
                f.write("%d,%d, %1.3f, %1.3f,%1.3f\n"% (FlowTime, NumberOfMovements, obj, lb,time.time()-StartTime))
                f.close()

                # read solution
                if file_export != "":
                    f = open(file_export)
                    s = f.readlines()
                    moves = eval(s[-1])   # read moves - check that this working with long output
                    f.close()

        else: # solution obtained by DP
            f = open('res_Hfull.csv','a')
            f.write("%d, %d, %1.3f, %1.3f, %1.3f\n"% ( T, load_movements_h, obj_h, obj_h, time.time()-StartTime))
            f.close()


        # Create script file
        if file_export != "":
            pickle.dump( (Lx, Ly, O, E,R,moves),open(scripts_path+"/script_full_%s_%d_%d_%d_%d_%d.p" % (MoveMethod, Lx, Ly,escort_num, load_num,rep),"wb"))