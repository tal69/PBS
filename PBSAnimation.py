#-------------------------------------------------------------------------------
# Name:        PBSAnimation
# Purpose:     Animiation of  mutli IO ponts (terminal) block and load movement variation
#              uses the new compact MT format of the DP table pickle
#
#
# Author:      Tal Raviv talraviv@tauex.tau.ac.il
#
# Created:     27-04-2018
# Copyright:   (c) TAL 2018
# Licence:     Free to use but please contact me  talraviv@tauex.tau.ac.il
#-------------------------------------------------------------------------------

from tkinter import *

import sys
import pickle
import PBSCom  as pz
import time
import copy
import random
import itertools


#random.seed(0)




class PathAnimation:
    def __init__(self, S, p, Lx, Ly, box_size=60,offset=40):
        self.Lx = Lx   # diminsions of the warehouses
        self.Ly = Ly
        self.S = S   # dcit indexed by states. Each entry is tuple (value of the state, optimal next state)
        self.p = p  # initial state
        self.box_size = box_size   # size of the squre representation of each load
        self.offset = offset
        #self.old_p = p

        self.seq = [p]  # history of the path for back setp operation

        self.toStop = False
        self.onRepeatMode = False
        self.onLoadRepeatMode = False

        self.time_step =0.25  # change this to control animation speed

        self.t = 0

        self.master = Tk()
        self.master.title("PBS-BM animation by Tal Raviv (2019)")

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


        self.random_button = Button(self.master, text = "Random", command= lambda: self.random_start())
        self.random_button.pack(fill=X)

        self.random_load_button = Button(self.master, text = "Random load repeat", command= lambda: self.random_load_repeat())
        self.random_load_button.pack(fill=X)

        self.randomRepeat_button = Button(self.master, text = "Random repeat", command= lambda: self.random_repeat())
        self.randomRepeat_button.pack(fill=X)

        self.t_text = StringVar()
        self.t_text.set("t = 0")
        self.label = Label(self.master, textvariable= self.t_text)
        self.label.pack()


        self.cnvs = Canvas(self.master,width=box_size*Lx+2*offset, height=box_size*Ly+2*offset, bg="white")
        self.cnvs.pack()

        self.s_text = StringVar()
        self.s_text.set("HI")
        self.label = Label(self.master, textvariable= self.s_text)
        self.label.pack()

        for x in range(Lx+1):
            self.cnvs.create_line (offset+x*box_size,offset, offset+x*box_size,offset+box_size*Ly)


        for y in range(Ly+1):
            self.cnvs.create_line (offset,offset+y*box_size, offset+box_size*Lx,offset+y*box_size)

        for t in Terminals:
            x,y = t
            self.cnvs.create_rectangle(self.offset+x*self.box_size, self.offset+(self.Ly-y-1)*self.box_size, self.offset+(x+1)*self.box_size, self.offset+(self.Ly-y)*self.box_size, width=0, fill="green")


        # Show initial state

        self.rect_ref = [[None for y in range(Ly)] for x in range(Lx)]
        self.rect = [None] * (Lx*Ly)

        self.draw_initial()

        self.master.mainloop()


    def draw_initial(self):
        self.E = pz.int2ListTuple(self.p, self.Lx,self.Ly)
        self.s_text.set(str(self.p))


        self.L = []
        for i in range (self.Lx*self.Ly):
            if self.rect[i] != None:
                self.cnvs.delete(self.rect[i])

        count = 0
        for x in range(self.Lx):
            for y in range(self.Ly):
                if not (x,y) in self.E:
                    self.rect[count] = self.cnvs.create_rectangle(self.offset+4+x*self.box_size, self.offset+4+(self.Ly-y-1)*self.box_size, self.offset-5+(x+1)*self.box_size, self.offset-5+(self.Ly-y)*self.box_size, fill="blue")
                    self.L.append((x,y))
                    self.rect_ref[x][y] = count
                    count += 1

        self.rect[count] = self.cnvs.create_rectangle(self.offset+4+self.E[0][0]*self.box_size, self.offset+4+(self.Ly-self.E[0][1]-1)*self.box_size, self.offset-5+(self.E[0][0]+1)*self.box_size, self.offset-5+((self.Ly-self.E[0][1]))*self.box_size, fill="red")
        self.rect_ref[self.E[0][0]][self.E[0][1]] = count

    def restart(self):
        #self.p = self.old_p
        self.p = self.seq[0]
        self.seq = self.seq[:1]
        self.draw_initial()
        if not self.onRepeatMode and not self.onLoadRepeatMode:
            self.s.set( "Start")
            self.step_button['state'] = 'normal'
            self.start_button['state'] = 'normal'
        self.t = 0
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


    def step_back(self):
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
        self.t += 1
        self.t_text.set("t="+str(self.t))

        if self.S[self.p][1]  == "Sink":
            if self.onRepeatMode:
                self.master.after(800, self.random_start)
            if self.onLoadRepeatMode:
                self.master.after(800, self.random_load_start)
            else:
                self.step_button['state'] = 'disabled'
                self.start_button['state'] = 'disabled'
                self.restart_button['state'] = 'normal'
                self.random_button['state'] = 'normal'
            return
        II = pz.int2ListTuple(self.S[self.p][1], self.Lx,self.Ly)[0]  # next location of the retreived load
        act = pz.state2Act(S,self.p,self.Lx,self.Ly)
        E1 = sorted([a[1] for  a in act])
        #E1 = [(self.E[i+1][0]+a[i][0], self.E[i+1][1]+a[i][1])   for i in range(len(a))]  # locations of the escorts on the next step
        #E0 = self.E[1:]

        moving = dict() # list of moving loads
        for i in range(len(act)):
            if act[i][0][0] < act[i][1][0]:  # escort moves right   (loads move left)
                for x in range(act[i][0][0]+1, act[i][1][0]+1):
                    moving[(x,act[i][0][1])] = (-1,0)
            elif act[i][0][0] > act[i][1][0]:  # escort moves left  (loads move right)
                for x in range(act[i][1][0], act[i][0][0]):
                    moving[(x,act[i][0][1])] = (1,0)
            elif act[i][0][1] < act[i][1][1]:  # escort moves up (loads move down)
                for y in range(act[i][0][1]+1, act[i][1][1]+1):
                    moving[(act[i][0][0],y)] = (0,-1)
            elif act[i][0][1] > act[i][1][1]:  # escort moves down   (loads move up)
                for y in range(act[i][1][1], act[i][0][1]):
                    moving[(act[i][0][0],y)] = (0,1)


        # Movoment annimation
        #print(moving)
        start_time = time.time()
        last_time = start_time

        #for i in range(self.box_size):

        delta_total= 0
        #while time.time()-start_time <= self.time_step:
        while delta_total < self.box_size:
            delta = (time.time()-last_time) * self.box_size / self.time_step

            delta_total += delta
            if delta_total > self.box_size:
                delta -= (delta_total- self.box_size)

            last_time = time.time()
            for (x,y) in moving:
                #Recall that Canvas (0,0) is the upper left corner but the warehouse (0,0) is lower left.
                #print(x,y,self.rect_ref[x][y],moving[(x,y)])
                if self.rect_ref[x][y] == None:
                    print("")
                self.cnvs.move(self.rect[self.rect_ref[x][y]],delta*moving[(x,y)][0],-delta*moving[(x,y)][1])
            self.cnvs.update()
            #time.sleep(0.001)



        # update referance


        ez = copy.deepcopy(self.rect_ref)
        for x,y in moving:
            self.rect_ref[x][y] = None

        for x,y in moving:
            self.rect_ref[x+moving[(x,y)][0]][y+moving[(x,y)][1]] = ez[x][y]

        self.E = copy.deepcopy([II]+E1)
        self.L = [(x,y) for x in range(self.Lx) for y in range(self.Ly) if not (x,y) in self.E]  # list of load locations


        self.p = pz.sortIntState(self.S[self.p][1] ,Lx, Ly)
        self.seq.append(self.p)
        self.s_text.set(str(self.p))


        if self.S[self.p][1]  == "Sink":
            if self.onRepeatMode:
                self.master.after(800, self.random_start)
            elif self.onLoadRepeatMode:
                self.master.after(800, self.random_load_start)
            else:
                self.step_button['state'] = 'disabled'
                self.start_button['state'] = 'disabled'
                self.restart_button['state'] = 'normal'
                self.random_button['state'] = 'normal'
                self.back_button['state'] = 'normal'

        else:

            #self.start_button['state']= 'normal'
            if cont:
                self.master.after(200, self.one_step, True)
            else:
                self.step_button['state'] = 'normal'



    def random_start(self):
        All =  list(itertools.product(range(self.Lx), range(self.Ly)))
        r = self.Lx*self.Ly
        item = random.randrange(1,r)
        (Ix, Iy) = All.pop(item)
        E = []
        k = len(pz.int2ListTuple(self.p, self.Lx, self.Ly)) -1
        for i in range(k):
            r -= 1
            ez = All.pop(random.randrange(0,r))
            E.append(ez)

        E.sort()

        #self.old_p = pz.listTuple2Int([(Ix,Iy)]+E, self.Lx, self.Ly)
        self.seq = [pz.listTuple2Int([(Ix,Iy)]+E, self.Lx, self.Ly)]

        self.restart()
        if self.onRepeatMode:
            self.one_step(True)


    # starting a randon load loop
    def random_load_start(self):

        while True:
            Ix, Iy = random.randrange(Lx), random.randrange(Ly)
            if not (Ix,Iy) in self.E:
                break

        self.seq = [pz.listTuple2Int([(Ix,Iy)]+self.E[1:], self.Lx, self.Ly)]
        #self.p =pz.listTuple2Int([(Ix,Iy)]+self.E[1:], self.Lx, self.Ly)

        self.restart()
        self.one_step(True)


    #  Repeatdly rodnomize an initial state show the optimal retrieval sequence for it

    def random_repeat(self):
        self.onRepeatMode = True
        self.s.set( "Stop")
        self.start_button['state'] = 'normal'
        self.restart_button['state'] = 'disabled'
        self.randomRepeat_button['state'] = 'disabled'
        self.random_load_button['state'] = 'disabled'
        self.back_button['state'] = 'disabled'
        self.random_button['state'] = 'disabled'
        self.random_start()


    # Repeatdly select a rodnomize load to retrieve and fetch it to the terminal
    # without chaning the location of the escorts after each retreival

    def random_load_repeat(self):
        self.onLoadRepeatMode = True
        self.s.set( "Stop")
        self.start_button['state'] = 'normal'
        self.restart_button['state'] = 'disabled'
        self.step_button['state'] = 'disabled'
        self.back_button['state'] = 'disabled'
        self.randomRepeat_button['state'] = 'disabled'
        self.random_load_button['state'] = 'disabled'
        self.random_button['state'] = 'disabled'
        self.random_load_start()


if __name__ == '__main__':
    if len(sys.argv) < 7 and len(sys.argv) != 2 and len(sys.argv) != 3:

        print("usage: python", sys.argv[0],"<model_name>  LM|BM <Ix> <Iy> <E1x> <E1y> , ...")
        print("For a given initial state\n")
        print("usage: python", sys.argv[0],"<model_name>  [LM|BM]")
        print("For randomly generated initial state with k escorts\n")
        exit(1)


    # cut the py extention for the import operation
    if sys.argv[1][-3:].upper()== ".PY":
        sys.argv[1] = sys.argv[1][:-3]


    exec("from "+sys.argv[1]+" import *")

    if len(sys.argv) < 3:
        ModelType = "LM"
    else:
        ModelType = sys.argv[2].upper()
        if not ModelType in ["LM", "BM"]:
            print('Panic: model type  (2nd argument) should be either LM or BM. Cannot be %s ' % sys.argv[2])
            exit(1)





    print("Loading file %s..." % (ModelType+"_"+sys.argv[1]+".p"), end="" )
    S = pickle.load( open( ModelType+"_"+sys.argv[1]+".p", "rb" ) )
    print("  done.")

    if len(sys.argv) >= 7:
        (Ix, Iy) = tuple([int(sys.argv[i]) for i in range(3,5)])


        L = [(int(sys.argv[2*i+5]), int(sys.argv[2*i+6])) for i in range(k) ]
        L.sort()
        L.insert(0,(Ix,Iy))


        if (not Ix in range(Lx)) or (not Iy in range(Ly)):
            print("Panic: initial item location is out of range (recall that the locations are indexed from 0")
            exit(1)

        p = pz.listTuple2Int(L, Lx, Ly)
        PathAnimation(S, p, Lx, Ly)
    else: # random start
        All =  list(itertools.product(range(Lx), range(Ly)))
        r = Lx*Ly
        item = random.randrange(1,r)
        (Ix, Iy) = All.pop(item)
        E = []
        for i in range(k):
            r -= 1
            ez = All.pop(random.randrange(0,r))
            E.append(ez)

        E.sort()

        p = pz.listTuple2Int([(Ix,Iy)]+E, Lx, Ly)
        PathAnimation(S, p, Lx, Ly)