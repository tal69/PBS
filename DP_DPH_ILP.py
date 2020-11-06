#-------------------------------------------------------------------------------
# Name:        DP_DPH_ILP.py
# Purpose:     Run the experiment with the full model (no replenishments)
#              Use heuristic solution as upper bound
#
# Author:      tal raviv,  talraviv@tau.ac.il
#
# Created:     23/08/2020, updated 18/9/2020, 27/10/2020
#              this version prints the lower bound even when MILP fails
# Copyright:   (c) Tal Raviv 2020
# Licence:     Free but please let me know that you are using it
#-------------------------------------------------------------------------------


import random
import sys
import itertools
import subprocess
import pickle
import time
from PBSCom import *
import PBS_DPHeuristic_lm
import PBS_DPHeuristic_bm
import os

scripts_path = "scripts_full_milp"


#file_export = "script_export"  # set to "" if no script file is needed (the typical situation for the experiment)
file_export = ""

""" consider getting this input from an external source """
alpha = 0; # C_max weight   - NOT RELEVANT IN THIS VERSION
beta = 1 # flowtime weight
gamma = 0.01 # movement weight
delta = 0.01 # queueing cost     - NOT RELEVANT IN THIS VERSION



# obtain command line paramteres

if len(sys.argv) < 11:
    print("Usage: python %s Lx Ly reps_range escorts_range DPTablesFile MoveMethod(LM|BM) skip_MILP_when_DP time_limit IO_location_list" % sys.argv[0])
    print("        DPTableFile contains ")

    exit(1)


Lx = int(sys.argv[1])
Ly = int(sys.argv[2])

reps_range = str2range(sys.argv[3])
load_num = 1 # int(sys.argv[4])
escorts_range = str2range(sys.argv[4])
DPTablesFile =  sys.argv[5]
MoveMethod = sys.argv[6].upper()

if not MoveMethod in ["LM", "BM"]:
    print("Panic: MoveMethod (6th argument) must be either LM or BM")


if sys.argv[7] == "1":
    skip_MILP_when_DP = True
else:
    skip_MILP_when_DP = False

time_limit = int(sys.argv[8])


# Get list of DP table files
f = open(DPTablesFile,"r")
DPFiles = f.readlines()
f.close()
DPFiles =[s.strip() for s in DPFiles]
Max_k_prime = len(DPFiles)
DPTableLoaded = False

ez = [int(a) for a in sys.argv[9:]]
O = []
for i in range(len(ez)//2):
    O.append((ez[i*2], ez[i*2+1]))

Locations =  sorted(set(itertools.product(range(Lx), range(Ly))))

S = [[]] * (Max_k_prime+1)

f = open('res_Hfull_and_DPH_%s_%dx%d.csv' % (MoveMethod,Lx,Ly),'a')
f.write("date, Regime, Lx x Ly, seed, #IOs, # Escorts, #Loads, IOs, Escorts, Target Loads, alpha, beta, gamma, Solution Method, Makespan, #load movments,  obj, CPU time\n" )
f.close()



for k in range(1, Max_k_prime+1):
        print("Loading DP file %s..."%DPFiles[k-1], flush=True)
        S[k] = pickle.load( open( DPFiles[k-1], "rb" ) )
        print("Done", flush=True)

for escort_num in escorts_range:

    for rep in reps_range:
        random.seed(rep)
        R,E = GeneretaeRandomInstance(rep, Locations, escort_num, load_num)
        problem_description = "%s, %s, %dx%d, %d, %d,%d,%d, %s, %s, %s, %1.3f, %1.3f, %1.3f" %\
            (time.ctime(),MoveMethod, Lx,Ly, rep, len(O), len(E), len(R), tuple_opl(O), \
            tuple_opl(E), tuple_opl(R) ,alpha,beta,gamma )




        for k_prime in range(1,min(Max_k_prime, escort_num)+1):
            StartTime = time.time()
            if MoveMethod == "LM":
                moves = PBS_DPHeuristic_lm.DOHueristicLM(S[k_prime],R[0],E, Lx,Ly, O,k_prime, False)
            else: # BM
                moves = PBS_DPHeuristic_bm.DOHueristicBM(S[k_prime],R[0],E, Lx,Ly, O,k_prime, False)

            T = len(moves)
            load_movements_h = sum([ len(a) for a in moves])
            obj_h = beta*T+load_movements_h*gamma

            #print("Used heuristic with k'=%d to find T=%d"%(min(Max_k_prime, escort_num), T), flush=True)

            if escort_num == k_prime:
                sol_method = "DP"
            else:
                sol_method = "DPH %d" % k_prime


            f = open('res_Hfull_and_DPH_%s_%dx%d.csv' % (MoveMethod,Lx,Ly),'a')
            f.write("%s, %s, %d, %d, %1.3f, %1.3f\n" %\
                (problem_description, sol_method, T, load_movements_h, obj_h, time.time() - StartTime ))
            f.close()


        if escort_num > Max_k_prime or not skip_MILP_when_DP:
            # StartTime = time.time()  This is deleted intenitally since we like to include the last DPH run in the MILP solution time

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

            # Delete the file to make sure that we read the new one
            if os.path.exists("out_pbs2b.txt"):
                os.remove("out_pbs2b.txt")

            try:
                subprocess.run(["oplrun", "pbs2b.mod", "pbs_full.dat"], check=True)
            except:
                print("Could not solve the model")

                f = open('res_Hfull_and_DPH_%s_%dx%d.csv' % (MoveMethod,Lx,Ly),'a')
                f.write("%s, MILP %ds, Panic: oplrun process failed, -, -, %1.3f\n " %\
                (problem_description, time_limit, time.time()-StartTime))
                f.write("%s, MILP-LB %ds, Panic: oplrun process failed, -, -, %1.3f\n " %\
                (problem_description, time_limit,  time.time()-StartTime))
                f.close()

                #f = open('res_Hfull.csv','a')
                #f.write("No solution, -,-,-, %1.3f\n" %(time.time()-StartTime))
                #f.close()
                continue  # skip to next instance without creating a script file
            else:
                f = open('res_Hfull_and_DPH_%s_%dx%d.csv' % (MoveMethod,Lx,Ly),'a')



                if os.path.exists("out_pbs2b.txt"):
                    exec(open("out_pbs2b.txt").read())  # Read the variables z,FlowTime, NumberOfMovements, obj, lb. Yes, I know this is ugly.

                    if obj != -1: # MILP found a feasible solution
                        f.write("%s, MILP %ds, %d, %d, %1.3f, %1.3f\n " %\
                        (problem_description, time_limit,  FlowTime, NumberOfMovements, obj, time.time()-StartTime))
                        f.write("%s, MILP-LB %ds, -, -, %1.3f, %1.3f\n " %\
                        (problem_description, time_limit, lb, time.time()-StartTime))
                    else: # MILP failes
                        f.write("%s, MILP %ds, No feasible solution found, -, -, %1.3f\n " %\
                        (problem_description, time_limit, time.time()-StartTime))
                        f.write("%s, MILP-LB %ds, -, -, %1.3f, %1.3f\n " %\
                        (problem_description, time_limit, lb, time.time()-StartTime))
                else:
                    f.write("%s, MILP %ds, Panic: Output file not created, -, -, %1.3f\n " %\
                    (problem_description, time_limit, time.time()-StartTime))
                    f.write("%s, MILP-LB %ds, Panic: Output file not created, -, -, %1.3f\n " %\
                    (problem_description, time_limit,  time.time()-StartTime))


                f.close()


                # read solution
                if file_export != "":
                    f = open(file_export)
                    s = f.readlines()
                    moves = eval(s[-1])   # read moves - check that this is working with long output
                    f.close()


        # Create script file
        if file_export != "":
            pickle.dump( (Lx, Ly, O, E,R,moves),open(scripts_path+"/script_full_%s_%d_%d_%d_%d_%d.p" % (MoveMethod, Lx, Ly,escort_num, load_num,rep),"wb"))