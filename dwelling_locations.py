#-------------------------------------------------------------------------------
# Name:        dewwling_pint
# Purpose:     Find all the optinal dewelling states for a settings
#              Assume that the relevant paths file exists
# Usage
# Author:      Tal Raviv
#
# Created:     15-04-2018, adapted to new DP file formats 28-08-2019
# Copyright:   (c) Tal Raviv 2018
# Licence:     Free but pleas contact me before use, talraviv@tauex.tau.ac.il
#-------------------------------------------------------------------------------

import pickle
import sys
import PBS_bm_mt as pz
import itertools

if not len(sys.argv) ==3:
    print("usage: python", sys.argv[0],"<model_name> <LM|BM>")
    exit(1)

# cut the py extention for the import operation
if  sys.argv[1][-3].upper() == ".PY":
    sys.argv[1] = sys.argv[1][:-3]

exec("from "+sys.argv[1]+" import *")

ModelType = sys.argv[2].upper()
if not ModelType in ["LM", "BM"]:
    print('Panic: model type (2nd argument) should be either LM or BM. Cannot be %s ' % sys.argv[2])
    exit(1)



config = {}

total_dist_lb = 0
for x in range(Lx):
    for y in range(Ly):
        dist = Lx+Ly+1
        for t in Terminals:
            dist = min(dist,abs(x-t[0]) + abs(y-t[1]))
        total_dist_lb += dist



S = pickle.load( open( ModelType+"_"+sys.argv[1]+".p", "rb" ) )
print("Start %s scanning %d states" % (sys.argv[1], len(S)))
for p,v in S.items():

    ez = pz.int2ListTuple(p, Lx, Ly)
    #Ix, Iy = ez[0]
    E = tuple(set(ez[1:]))

    if E in config:
        config[E] += v[0]
    else:
        config[E] = v[0]


minimal_distance = config[min(config, key=config.get)]
maximal_distance = config[max(config, key=config.get)]
expected_distance = sum(list(config.values())) / len(list(config.values()))

print("")
print("Dwelling points for ",Lx,"x",Ly," puzzle with ", k, "escorts and terminal locations %s"% Terminals)
print("----------------------------------------------------")
print ("Average distance for the best dwelling points configuaration of ",k,"escorts is %1.3f" %( minimal_distance/ (Lx*Ly-k)))
print ("Expected distance for a random set of dwelling points of ",k,"escorts is %1.3f " %(expected_distance/ (Lx*Ly-k)))
print ("Average distance for the worst dwelling points configuaration  of ",k,"escorts is %1.3f " %( maximal_distance/ (Lx*Ly-k)))
print("Naive LB for average retival time %1.3f" % (total_dist_lb / (Lx*Ly)) )

print("The optimal conigurations are:")

print("")
count = 0
for d, v in config.items():
    if minimal_distance == v:
        count +=1
        for y in range(Ly-1,-1,-1):
            for x in range(Lx):
                if  (x,y) in d:
                    print(".",end="")
                elif (x,y) in Terminals:
                    print('T', end="")
                else:
                    print("*",end="")
            print("")
        print("")
print("Number of optimal dwelling configurations: ", count)

print ("%1.3f, %1.3f, %1.3f, %1.3f" %( minimal_distance/ (Lx*Ly-k), expected_distance/ (Lx*Ly-k), maximal_distance/ (Lx*Ly-k), total_dist_lb / (Lx*Ly)))
