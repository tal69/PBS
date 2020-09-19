#-------------------------------------------------------------------------------
# Name:        Puzzle_lm_mt

# Purpose:     Solve the Puzzle-bases storage problem with simultanious block movment and multi terminals
#              This version use a forbiden table to save time when checking escorts
#              Conflicts
#              decision are stored as integers that represents states in the same order
#              as the representation of the states
#              this allows easily deriving the actual escrots that are moving
#              but requires sorting the decision before using the to retrieve the
#              next state
#
# Usage        Command line : python pbs_lm_mt <setting file name>
#              Imported as a module to provide encoding and presentation facilities
# Author:      Tal Raviv
#
# Created:     30 Aug, 2019, minor updates 1 May 2020
# Copyright:   (c) Tal Raviv 2019
# Licence:     Free but please contact me talraviv@tauex.tau.ac.il
#
#-------------------------------------------------------------------------------

import time
import itertools
import pickle
import sys
#import math
import create_forbid_table_lm as cft
from PBSCom import *



# The function create the DP solution of Lx by Ly warehouse with k escorts
def puzzle_solve(Lx , Ly ,k, Terminals, name, min_energy=False):


    # Open the pickle file with all the forbiden escorts pair movments
    # F is a set of   { {O0,D0}, {O1,D1} } entries
    #  Where O0, D0, O1, D1 are tuples of origns and destinatns

    F = cft.create_forbid_table((Lx,Ly))

    # The number of all possible states. Just for reporting and QA
    numberOfStates = (Lx*Ly)*nCr(Lx*Ly-1,k)

    start_time = time.time()
    interval_time = time.time()

    # Create the set of all the locations in the warehouse as 2-tuples
    Locations =  set(itertools.product(range(Lx), range(Ly)))

    # Intitalize the list dictionaries (hash-table) that holds all the states
    S = [dict()]

    # Initialize the table of optimal action at each state

    # Create all initial states (S_0) where the retrieved load is at the terminals
    print("Creating S[0] states...",end="", flush=True)

    # The set of the locations that are candidates for esecorts
    R = Locations

    # Scan through all the possible combination of k escrot locations in R
    for e in itertools.combinations(R, k):
        e1 = sorted(e)           # we need this for the encoding


        for t in Terminals:
            if not t in e:
                n = listTuple2Int([t]+e1,Lx,Ly)
                if min_energy:
                    S[0][n] = (None,0)
                else:
                    S[0][n] = None  # Marks the sink (in othe states we will have the optimal action here)

    count = len(S[0])  # The number of states created so for (for repeoring in QA only)
    dist=0  # The current index of the list S  (which is the value of the created state in the subset S[dist].

    print("%d states created (%1.1f %% completed in %1.1f sec.) " % (len(S[dist]),100*count/numberOfStates,time.time() - start_time))


    while count < numberOfStates:  # just for QA?
        print("Creating S[%d] states..." % (dist+1), end="")
        S.append(dict())  # create another entry in the list of dictionaries that holds S[0],S[1],...

        if not S[dist]:  # the dictionary is empty  - only for QA
            print("Panic: the number of enumerated stats seems smaller thane xpected")
            exit(1)

        for cs in S[dist]:  # scan all the state in the previous dictionary


            # convert to encoded state to a list of location
            ez0 = int2ListTuple(cs, Lx, Ly)
            I = ez0[0]   # the loaction of the retrieved load
            E = ez0[1:]  # the locations of the escorts

            if E == [(0, 0), (1, 1), (1, 1)]:
                print("bug")


            # Generatae all escort movment combinations ( stay, right,letf, up, down )
            # using a search tree
            Tree = [];
            nextE = []  # the locations of the escorts after the current movement

            while True:

                curr = len(nextE)  # the number of moving escorts in the current action

                # this condition will hold only after few iterations of the outer loop after the tree
                # contains enties with decisions about the movments of all the enteries
                # If a shorter entry is poped from the tree it will be extended in the else part of this condition
                if curr == k:

                    move = [0,0] # the null move (i.e., no escrot move)

                    for ii in range(2*k):   # loops through all the combinations of  escorts and directions (horizontal or vertical)
                        i,d = divmod(ii,2)  # need this trick to avoid nested loops so break can get me out of here
                        # is the index of the moving escort and d of the direction (0=horizontal, 1=vertical ??)

                        if nextE[i][1-d] == I[1-d] and nextE[i][1-d] == E[i][1-d]: # item moves horizontaly (resp. vert)  only if the escort and the item are on the same row (resp. col)
                            if E[i][d] < nextE[i][d] and I[d] <= nextE[i][d] and I[d] > E[i][d]:   # Escort move left /down
                            # Example escort moves 10 -> 5, item is initially at 7 -> item moves to 8
                                move[d] = -1  # item moved right/up  (so previous location is left/up)
                                break
                            elif E[i][d] > nextE[i][d]  and I[d] >= nextE[i][d] and I[d] < E[i][d]:   # Escort move right  / up
                            # Example escort moves 5 -> 10, item is initially at 7 -> item moves to 6
                                move[d] = 1  # item moves down/left
                                break


                    II = (I[0]+move[0],I[1]+move[1])   # the new coordinate of the retrieved load after the current move

                    if II in nextE:  # just for debugging
                        print("Panic: the req load was moved to a new location of an an escort")
                        exit(-1)

                    if II[0] < 0 or II[1] <0:   # just for debugging
                        print("Panic: iligal move", move)
                        exit(-1)


                    n1 = listTuple2Int([II]+sorted(nextE),Lx,Ly)  # calculate the id of the new candidate state

                    if n1 ==    348179:
                        print("bug")


                    # update the first state that brings the warehouse from a state in S[dist+1] to the current state (in S[dist]

                    if min_energy:
                        if not AlreadyInDicts(S,dist-1,dist,n1):
                            total_energy = sum(abs(E[i][0]-nextE[i][0])+ abs(E[i][1]-nextE[i][1])  for i in range(len(E)))

                            if n1 in S[dist+1]:
                                if total_energy < S[dist+1][n1][1]:
                                    S[dist+1][n1]=  (listTuple2Int([I] + [a[1] for a in sorted(list(zip(nextE,E)))],Lx, Ly),total_energy)
                            else:
                                S[dist+1][n1]=  (listTuple2Int([I] + [a[1] for a in sorted(list(zip(nextE,E)))],Lx, Ly),total_energy)
                    else:
                        if not AlreadyInDicts(S,dist-1,dist+1,n1):
                            S[dist+1][n1]=  listTuple2Int([I] + [a[1] for a in sorted(list(zip(nextE,E)))],Lx, Ly)


                            # just for debuging  remove lagter
                            #if not checkComp(n1,S[dist+1][n1],Lx,Ly):
                            #    raise  TypeError("Not comp")


                else:  # curr != k   (meaning that we did not decide about the movments of each of the escorts yet
                    # her we will extend the lengh of  the entry by a decison about one movement and reinsert it to the tree


                    # creat all possible horizontal movment of curr escort
                    for x in [max(0,E[curr][0]-1),E[curr][0],min(Lx-1,E[curr][0]+1)]:
                        prev_pos = (x,E[curr][1])  # we call it prev_pos but in the DP it is actually the next to be scanned

                        # check if cross the movment of a pervious moving escort (in the forbiden table)
                        # we don't check about collosion with escorts that we didn't decide about their movment yet
                        # but this will be catched when we make the decision about them
                        Cross= False

                        if nextE == [(0, 2), (1, 3)] and  prev_pos == (1,3):
                            #print("bug")
                            pass


                        for i in range(curr):
                            #if E[curr] == (1,1):
                                #print("bug")
                            if cft.te(E[curr],prev_pos , E[i],nextE[i]) in F:
                                Cross=True
                                break

                        if not Cross:  # if there is no colusion, add an entry to the tree
                            #if set(nextE) == set([(0,0),(1,1)]) and prev_pos == [(1,1)]:
                            #if prev_pos in nextE:
                            #    print("bug")

                            Tree.append(nextE+[prev_pos])


                    # create all possible vertical movment of curr escort
                    for y in [max(0,E[curr][1]-1),min(Ly-1,E[curr][1]+1)]:
                        prev_pos = (E[curr][0],y)  # we call it prev_pos but in the DP it is actually the next to be scanned
                        Cross= False
                        for i in range(curr):
                            #if (E[curr][0],E[curr][1], E[curr][0],y, E[i][0], E[i][1], nextE[i][0], nextE[i][1] )  in F:
                            if cft.te(E[curr], prev_pos, E[i],nextE[i]) in F:
                                Cross=True
                                break

                        if not Cross:  # if there is no colusion, add an entry to the tree
                            #if set(nextE) == set([(0,0),(1,1)]) and prev_pos == [(1,1)]:
                            if prev_pos in nextE:
                                print("bug")
                            Tree.append(nextE+[prev_pos])


                if Tree:  # pop the next item from the tree for the next iteration
                    nextE = Tree.pop()  # in the next itearion it will either be used to craete a new state or further extended
                else:
                    break  # if the tree is empty, we can break out of the while loop, no more action to evaluate for the current state

        dist += 1   # Update the diatcne from the final state after handling all the states of S[dist]
        count += len(S[dist])  # Update our count of created staes
        print("%d states created (%1.1f %% completed in %1.1f sec.)" % (len(S[dist]),100*count/numberOfStates,time.time() - start_time))

    print("\nCalculation time %1.3f seconds ---" % (time.time() - start_time))
    print("Number of states scanned %d / %d" % (count, numberOfStates))

    print("Mergining and saving to files...")
    start_time = time.time()
    C = dict()
    for i in range(len(S)):
        for k,e in S[i].items():
            if k in C:  # for deubugging only
                print("Panic", k,e,int2ListTuple(k,Lx,Ly),int2ListTuple(e,Lx,Ly),i, C[k])
                exit(-1)
            if i == 0:
                C[k] = (0,"Sink")
            else:
                if min_energy:
                    C[k] = (i,e[0])
                else:
                    C[k] = (i,e)
        S[i] = None  # release the memory


    pickle.dump( C, open( "LM_"+name, "wb" ) )


    print("Saving time %1.3f seconds---" % (time.time() - start_time))




if __name__ == '__main__':
    if not len(sys.argv) in [2,3]:
        print("usage: python", sys.argv[0],"<Settings file name>  [0|1]")
        print("              1 - min energy (default) 0 - first best ")
        exit(1)

    # cut the py extention for the import operation
    if sys.argv[1][-3:] == ".py" or sys.argv[1][-3] == ".PY":
        sys.argv[1] = sys.argv[1][:-3]

    if len(sys.argv)==3 and sys.argv[2] == "0":
        me = False
    else:
        me = True


    exec("from "+sys.argv[1]+" import *")


    if (k>= Lx*Ly):
        print("Panic: more escorts and items than cells in the grid")
        exit(1)


    puzzle_solve(Lx,Ly,k,Terminals, sys.argv[1]+".p", min_energy=me)
