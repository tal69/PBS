/*********************************************
 * OPL 12.10.0.0 Model
 * Author:a Tal Raviv
 * Creation Date: Aug 4, 2020 at 9:42:18 PM
 * The load movement model of Section 4 in the paper (with replenishments)
 * This model is designed run repeatdly. Each run is one role of the horizon
 * The post script overide the file "InitLoc.dat" that holds the initial (current) locations of the escorts and the retrieved loads
 * The file out.txt is created with the solution at the last row as a pythonic list
 * Each item in the list is a list of the block movments occured in the corrosponding time step, where each movement is a tuple 
 * ((orig_x,orig_y), (dest_x, dest_y)) 
  
 *********************************************/

execute {cplex.tilim = 120;}

string file_export = ...;

float alpha = ...; // C_max weight
float beta = ...; // flowtime weight
float gamma = ...; // movement weight
float delta = ...; // queueing cost

float incentive = ...;

tuple Loc {
  key int x;
  key int y;
} 

 tuple Move {
   key int orig_x;
   key int orig_y;
   key int dest_x;
   key int dest_y;
   float cost;
}

int Lx = ...;
int Ly = ...;
int T  = ...;  // planning horizon

int TT = ...; // sliding window time

range Tr = 0..T;
range commodityType = 1..2;  // 1 retrieved load, 2 blocking load

{Move} moves = {};
{Loc} locations = {};
{Loc} E = ...; // set of initial escort  initial locations
{Loc} O = ...;  // Output points locations
{Loc} I = ...;

{int} RT[I] = ...; // release times at each of the input locations
{Loc} R = ...;  // Set of retrived item initial locations

int ofset_time = ...;


{Loc} NextE;
{Loc} NextR;

int ISupply[I,Tr]; // supply of the feeding nodes;

execute {
  for (var x = 0; x < Lx; x++) for (var y = 0; y < Ly; y++) {
    locations.add(x,y);
    if (x< Lx-1)  moves.add(x,y,x+1,y, gamma); // right
    if (y< Ly-1)  moves.add(x,y,x,y+1, gamma);  // up
    if(x>0) moves.add(x,y,x-1,y, gamma);  // left
    if(y>0) moves.add(x,y,x,y-1, gamma);  //down
    moves.add(x,y,x,y, 0);  // stand still     
  }
  for (var l in I) for (var t in RT[l]) ISupply[l][t] = 1;
}

{Loc} B = locations diff E diff R;  // initial location of the blocking loads


float dist[locations];

execute {
  for(var l0 in locations) {    
    var min_dist = 9999;
    for (var l in O) {
      var ez = 6* Math.min(Math.abs(l0.x-l.x), Math.abs(l0.y-l.y))  + 
      5 * (Math.max(Math.abs(l0.x-l.x), Math.abs(l0.y-l.y))-Math.min(Math.abs(l0.x-l.x), Math.abs(l0.y-l.y)));
      if (ez < min_dist)  min_dist = ez      
    }
    dist[l0] = min_dist;
  }
}


float supply[l in locations][i in 1..2] = 0;

execute {
  for (var l in R) supply[l][1] = 1;   // supply of retrieved loads   
  for (l in B) supply[l][2] = 1;  // supply of blocking loads
}


// Handle lonley loads
float direction[moves];
execute {
  	// find distance to closest escort
  	for (var r in R) {  
  	var min_dist = Lx+Ly+1;
  		for (var e in E) {
  	  	var ez = Math.abs(r.x-e.x)+ Math.abs(r.y-e.y);
  	  	if (ez < min_dist)  	min_dist = ez
    }
    if (min_dist >= T-2)  {  //movements toward this load should be incentiviesed
    	for (var m in moves) {
    	  if (m.orig_x < r.x && m.orig_x > m.dest_x || m.orig_x > r.x && m.orig_x < m.dest_x || 
    	  m.orig_y < r.y && m.orig_y > m.dest_y || m.orig_y > r.y && m.orig_y < m.dest_y) direction[m] = direction[m]- incentive;
    	}
    	  
    	}  
	}	
}

dvar boolean x[moves,Tr,commodityType];  // flow on movement arcs
dvar boolean q[O,Tr];  // flow on sink arcs
dvar boolean xi[I,Tr]; // flor on the idling arcs of the feeding buffers
dvar boolean xr[I,Tr]; // flor on the replensihment arcs of the feeding buffers
dvar float+ z;

dexpr float u[l in locations] = sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,T,1];  // flow from the last layer to the sink of commodity 1

dexpr int RR[l in locations] = sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,TT-1,1];  // locations of the retrived loads
dexpr int BB[l in locations] = sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,TT-1,2];  // locations of the blocking loads



minimize alpha* z + sum(m in moves, t in Tr, i in 1..2 )  m.cost   *x[m,t,i] +
				sum(m in moves, t in Tr)  direction[m]  *x[m,t,2] + 
				beta * sum(l in O, t in Tr) t* q[l,t]
                + delta * sum (l in I,t in Tr) xi[l,t] +  
                beta* sum(l in locations) (T+dist[l])* u[l];

subject to{
  // (2) in the paper
  // Flow conservation at nodes for retrived loads (commodity 1)
  forall ( l in locations, t in 1..T) sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,t-1,1]  == 
  	 sum( m in moves : m.orig_x == l.x && m.orig_y == l.y) x[m,t,1] +
  	 sum(l1 in O :l1 == l ) q[l1,t];
  	 
  //Flow conservation at nodes for blocking loads (commodity 2) 
  forall ( l in locations, t in 1..T) sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,t-1,2] + sum(l1 in I: l1 == l)  xr[l,t-1] == 
  	 sum( m in moves : m.orig_x == l.x && m.orig_y == l.y) x[m,t,2];
  	 
 // flow conservation at the feeding buffers
  forall ( l in I, t in 1..T) xi[l,t-1] +ISupply[l,t] == xi[l,t] + xr[l,t];  
  
  // Flow conservation at t= 0
  forall ( l in O ) supply[l,1] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,1] + q[l,0];
  forall ( l in locations diff O ) supply[l,1] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,1];
  forall ( l in locations) supply[l,2] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,2];
  forall ( l in I) ISupply[l,0] == xi[l,0] + xr[l,0];
  
  // Buffers empty at the end  (like deleting the last idling arc)
  forall ( l in I) xi[l,T] == 0;
 
  // Flow conservation at the sink
  sum(l in O, t in Tr) q[l,t]  + sum(l in locations) u[l]  == card(R);
   
  // Generalized capacitiy constraint
  forall ( l in locations, t in Tr )  
  	sum(i in 1..2,  m in moves : m.dest_x == l.x && m.dest_y == l.y ) x[m,t,i]  + sum(l1 in I: l1 == l)  xr[l,t]  <= 1;

  // constraint - avoid conflicts
  forall ( l in locations, t in Tr )  
  	sum(i in 1..2,  m in moves : m.dest_x == l.x && m.dest_y == l.y && (m.orig_x != l.x || m.orig_y != l.y )) x[m,t,i] 
  	+ sum( l1 in O :l1 == l ) q[l1,t] + sum(l1 in I: l1 == l)  xr[l,t]
  	+ sum(i in 1..2,  m in moves : m.orig_x == l.x && m.orig_y == l.y && (m.dest_x != l.x || m.dest_y != l.y )) x[m,t,i] <= 1;
    	
   // No swap - possible cut?
  //forall( m in moves, t in 0..T-1 : m.orig_x != m.dest_x || m.orig_y != m.dest_y) sum(i in 1..2) (x[m,t,i] + 
   //x[<m.dest_x, m.dest_y, m.orig_x, m.orig_y>,t,i]) <= 1; 
  
   // ( stipulating z
   if (alpha > 0 )  {
     forall( l in O,t in Tr)  t * q[l,t] <= z;
     forall (l in locations) (T+dist[l]) * u[l] <= z;
     
   }  else {
     z == 0; // just to avoid warning
   }  
   
   // exaple of lonely load sum(m in moves : m.orig_x == 8 && m.orig_y == 8) x[m,T,2] == 0;
   
}

execute {
  
  var t;
  var l

  for(t in Tr) {
  	for (l in O)  {  
	  	if (q[l][t] == 1) {
	   		writeln("At time ",ofset_time+t+1," item retrived via output location",l);
	 	
	 	}
	}	 
	for (l in I)  {
	 	if  (xr[l][t] == 1) {
	 	  	writeln("At time ",ofset_time+t+1," item replenished via input location",l);
	
		}		 	  
 	}
 }  
  
 for (l in locations)  {
   if (u[l] > 0.99)
   writeln("At time T=",ofset_time+T," item arrived at location location",l);
 }	
  
  if (file_export != "") {
	  var f = new IloOplOutputFile(file_export);
	  // Write the input and output in a format readable by our animation rutine and for the handling script
	  
	  f.writeln(Lx,",", Ly)
	  // B
	  f.write("[");
	  var lFirst = true
	  for (l in B ) {
	    if (!lFirst) { 
	    	f.write(",");
	    	lFirst = false
	  	}     
	  	f.write("(", l.x,",", l.y,")");
	  }  
	  f.writeln("]");
	  
	  // R
	  f.write("[");
	  var lFirst = true
	  for (l in R ) {
	    if (!lFirst) { 
	    	f.write(",");
	    	lFirst = false
	  	}     
	  	f.write("(", l.x,",", l.y,")");
	  }  
	  f.writeln("]");
	  
	  // O
	  f.write("[");
	  var lFirst = true
	  for (l in O ) {
	    if (!lFirst) { 
	    	f.write(",");
	    	lFirst = false
	  	}     
	  	f.write("(", l.x,",", l.y,")");
	  }  
	  f.writeln("]");
	  
	  
	  f.write("[")
	  for(t=0 ; t< TT; t++) {
	    f.write("[");
	    var first = true;
	    for (var  m in moves) {
	      
	      if ((m.orig_x != m.dest_x  || m.orig_y != m.dest_y) && x[m][t][1] +x[m][t][2]  > 0.99) {
	        if (first)
	      		first = false;
	      	else
	      		f.write(",")   
	      	f.write("((",m.orig_x, ",", m.orig_y,"),(", m.dest_x, ",",m.dest_y, "))"); 
	      }      
	    }
	    
	    for (l in O) if( q[l][t] > 0.99) {
	       if (first)
	      		first = false;
	      	else
	      		f.write(",")   
	       f.write("((",l.x, ",", l.y,"),(None, None))");
        }
         
        for (l in I) if (xr[l][t] > 0.99) {
          if (first)
	      		first = false;
	      	else
	      		f.write(",")   
	       f.write("((None, None),(",l.x, ",", l.y,"))");
        }
	    
	    if (t < TT-1)
	    	f.write("],");        
	    else
	    	f.write("]]");   
	  }
	  f.close();
	}  //export	 
	  
	 // Create input for the next iteration
	for ( l in locations) {
	  if (BB[l] < 0.001 && RR[l]<0.001) NextE.add(l);
	  if (RR[l] > 0.999) NextR.add(l);
	}
	
	f = new IloOplOutputFile("InitLoc.dat");
	f.writeln("E=",NextE,";");
	f.writeln("R=",NextR,";");
	f.writeln("RT=[];");
	f.writeln("ofset_time=",ofset_time+TT,";");
	f.close();
}