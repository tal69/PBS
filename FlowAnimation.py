#-------------------------------------------------------------------------------
# Name:        FlowAnimation
# Purpose:     Annimation of a script produced by Rolling, ExperimentFull
#              also work for the solution of the DP based heuristic
#              (adapted from previous version of KivaAnnimation
#
#
# Author:      Tal Raviv talraviv@tau.ac.il
#
# Created:     22-8-2020
# Copyright:   (c) TAL 2020
# Licence:     Free to use but please contact me  talraviv@tau.ac.il
#-------------------------------------------------------------------------------

from tkinter import *

import sys
import pickle
import time
import copy
import random
import itertools
import pickle



class PathAnimation:
    def __init__(self, box_size=60,offset=40):
        self.Lx = L[0]   # diminsions of the warehouses
        self.Ly = L[1]

        if max(L[0],L[1]) > 10:
            box_size = 600 // max(L[0],L[1])

        self.L = L
        self.k = len(E)
        self.t = 0

        self.R, self.E = R,E
        self.Rsav, self.Esav  = copy.copy(R),copy.copy(E)
        #Esav is probably redundent now because we don't update self.E anymore


        self.box_size = box_size   # size of the squre representation of each load
        self.offset = offset

        self.toStop = False
        self.onRepeatMode = False
        self.onLoadRepeatMode = False

        self.time_step =0.35  # change this to control animation speed


        self.master = Tk()
        self.master.title("PBS-Flow animation by Tal Raviv (2020)")

        self.s = StringVar()


        self.s.set( "Start")

        self.start_button = Button(self.master, textvariable= self.s, command= lambda: self.start())
        self.start_button.pack(fill=X)


        self.step_button = Button(self.master, text = "One Step", command= lambda: self.one_step())
        self.step_button.pack(fill=X)


        self.back_button = Button(self.master, text = "Step back", command= lambda: self.step_back())
        self.back_button.pack(fill=X)

        self.restart_button = Button(self.master, text = "Restart", command= lambda: self.restart())
        self.restart_button.pack(fill=X)


        self.t_text = StringVar()
        self.t_text.set("t = 0")
        self.label = Label(self.master, textvariable= self.t_text)
        self.label.pack()


        self.cnvs = Canvas(self.master,width=box_size*L[0]+2*offset, height=box_size*L[1]+2*offset, bg="white")
        self.cnvs.pack()


        for x in range(self.Lx+1):
            self.cnvs.create_line (offset+x*box_size,offset, offset+x*box_size,offset+box_size*self.Ly)


        for y in range(self.Ly+1):
            self.cnvs.create_line (offset,offset+y*box_size, offset+box_size*self.Lx,offset+y*box_size)

        for t in O:
            x,y = t
            self.cnvs.create_rectangle(self.offset+x*self.box_size, self.offset+(self.Ly-y-1)*self.box_size, self.offset+(x+1)*self.box_size, self.offset+(self.Ly-y)*self.box_size, width=0, fill="green")


        # Show initial state

        self.LoadsRef = [[None for y in range(self.Ly)] for x in range(self.Lx)]


        self.draw_initial()

        self.master.mainloop()


    def draw_initial(self):


        # Draw regular loads in blue and store load intitial references
        #count_load = 0
        for x in range(self.Lx):
            for y in range(self.Ly):
                if self.LoadsRef[x][y]  != None:
                    self.cnvs.delete(self.LoadsRef[x][y])
                    self.LoadsRef[x][y] = None



        for x in range(self.Lx):
            for y in range(self.Ly):
                if not (x,y) in self.E:
                    if  not (x,y) in self.R:
                        self.LoadsRef[x][y] = self.cnvs.create_rectangle(self.offset+4+x*self.box_size, self.offset+4+(self.Ly-y-1)*self.box_size, self.offset-5+(x+1)*self.box_size, self.offset-5+(self.Ly-y)*self.box_size, fill="blue")
                    else:
                        self.LoadsRef[x][y] = self.cnvs.create_rectangle(self.offset+4+x*self.box_size, self.offset+4+(self.Ly-y-1)*self.box_size, self.offset-5+(x+1)*self.box_size, self.offset-5+((self.Ly-y))*self.box_size, fill="red")



    def restart(self):

        self.t = 0

        self.R, self.E =copy.copy( self.Rsav), copy.copy(self.Esav)

        self.draw_initial()

        self.s.set( "Start")
        self.step_button['state'] = 'normal'
        self.start_button['state'] = 'normal'
        self.t_text.set("t="+str(self.t))

    def start(self):
        if self.s.get() == "Start":
            self.s.set( "Stop")
            self.restart_button['state'] = 'disabled'
            self.back_button['state'] = 'disabled'
            self.one_step(cont=True)

        else:
            self.s.set( "Start")
            self.restart_button['state'] = 'normal'
            self.step_button['state'] = 'normal'
            self.random_button['state'] = 'normal'
            self.randomRepeat_button['state'] = 'normal'
            self.random_load_button['state'] = 'normal'
            self.back_button['state'] = 'normal'
            self.toStop = True
            self.onRepeatMode = False
            self.onLoadRepeatMode = False


    def step_back(self):  # Currently not working
        if self.t >0:
            self.t -= 1
            self.t_text.set("t="+str(self.t))

            self.p = self.seq[-2]
            self.seq = self.seq[:-1]
            self.draw_initial()
            self.step_button['state'] = 'normal'
            self.s.set( "Start")
            self.start_button['state'] = 'normal'


    def one_step(self, cont=False):

        if self.toStop:
            self.toStop = False
            return
        self.step_button['state'] = 'disabled'
        #self.start_button['state'] = 'disabled'
        #self.t += 1
        self.t_text.set("t="+str(self.t))

        if self.t  == len(moves):
            self.step_button['state'] = 'disabled'
            self.start_button['state'] = 'disabled'
            self.restart_button['state'] = 'normal'
            return



         #   movment handles
        dirL = []
        Load_handle = []

        for mv in moves[self.t]:
            if mv[1] == (None, None):  # item is being ejected
                dirL.append ((0,0))
            else:
                dirL.append ( (mv[1][0]-mv[0][0], mv[1][1]-mv[0][1]))
            Load_handle.append(self.LoadsRef[mv[0][0]][mv[0][1]])



        #print (dirA)

        # Movoment annimation
        start_time = time.time()
        last_time = start_time


        delta_total= 0
        while delta_total < self.box_size:
            delta = (time.time()-last_time) * self.box_size / self.time_step
            delta_total += delta
            if delta_total > self.box_size:
                delta -= (delta_total- self.box_size)
            last_time = time.time()

            for i in range(len(Load_handle)):
                if dirL[i] != (0,0):
                    self.cnvs.move(Load_handle[i],delta*dirL[i][0],-delta*dirL[i][1])

            self.cnvs.update()
            time.sleep(0.001)

        # First clear old handls
        for mv in moves[self.t]:
            self.LoadsRef[mv[0][0]][mv[0][1]]= None

        # Then update new ones
        for i in range(len(moves[self.t])):
            mv_dest = moves[self.t][i][1]
            if mv_dest != (None, None):
                self.LoadsRef[mv_dest[0]][mv_dest[1]] = Load_handle[i]
            else:
                self.cnvs.delete( Load_handle[i])




        self.t += 1
        self.t_text.set("t="+str(self.t))

        print (self.t)
        if self.t == len(moves):
            self.step_button['state'] = 'disabled'
            self.start_button['state'] = 'disabled'
            self.restart_button['state'] = 'normal'
            self.back_button['state'] = 'normal'

        else:
            if cont:
                self.master.after(200, self.one_step, True)
            else:
                self.step_button['state'] = 'normal'





if __name__ == '__main__':
    if len(sys.argv) != 2:

        print("usage: python", sys.argv[0],"<script_name.p> ")
        exit(1)


    # cut the py extention for the import operation
    if sys.argv[1][-2:].upper()!= ".P":
        sys.argv[1] += ".p"


    Lx, Ly, O, E,R,moves = pickle.load( open(sys.argv[1],"rb"))

    L = [Lx,Ly]


    PathAnimation()

