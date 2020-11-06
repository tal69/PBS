/*********************************************
 * OPL 12.10.0.0 Model
 * Author:a Tal Raviv
 * Creation Date: Aug 4, 2020 at 9:42:18 PM
 * This is the mathmatical model presented in Bukchin & Raviv (2020) for both LM and BM regimes.
 * Same as pbs2.mod but do not print the problem demographic into the result file.
 * Insead, the solution information is printed into a file that can be executed by pyhton
 *********************************************/

float time_limit = ...;
execute {cplex.tilim = time_limit; } 
string MoveMethod = ...;  // can be LM or BM
string file_export = ...;

float alpha = ...; // C_max weight
float beta = ...; // flowtime weight
float gamma = ...; // movement weight

// for the signle item case use alpha=0 and beta = 1, gamma = small numberש

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
int T  = ...;

range Tr = 0..T;
range Xr = 0..Lx-1;
range Yr = 0..Ly-1;

{Move} moves = {};

{Loc} locations = {};

{Loc} E = ...; // set of initial escort  initial locations
{Loc} R = ...;  // Set of retrived item initial locations  - for now use only one item
{Loc} B = locations diff E diff R;  // initial location of the blocking loads
{Loc} O = ...;  // Output points locations

{int} Dirs = {-1, 1}; // directions

execute {
  for (var x in Xr) for (var y in Yr) {
    locations.add(x,y);
    if (x< Lx-1)  moves.add(x,y,x+1,y, gamma); // right
    if (y< Ly-1)  moves.add(x,y,x,y+1, gamma);  // up
    if(x>0) moves.add(x,y,x-1,y, gamma);  // left
    if(y>0) moves.add(x,y,x,y-1, gamma);  //down
    moves.add(x,y,x,y, 0);  // stay still 
  }
}

float supply[l in locations][i in 1..2] = 0;

execute {
  for (var l in R) supply[l][1] = 1;   // supply of retrieved loads   
  for (l in B) supply[l][2] = 1;  // supply of blocking loads
}


dvar boolean x[moves,Tr,1..2];  // flow on movement arcs
dvar boolean q[O,Tr];  // flow on sink arcs
dvar float+ z;


dexpr float NumberOfMovements = (sum(m in moves, t in Tr, i in 1..2 )  m.cost  *x[m,t,i])/gamma;
dexpr float FlowTime = sum(l in O, t in Tr) t* q[l,t];  



minimize alpha* z + sum(m in moves, t in Tr, i in 1..2 )  m.cost  *x[m,t,i] + beta * FlowTime;

subject to{
  // (2) in the paper
  // Flow conservation at nodes for retrived loads (commodity 1)
  forall ( l in locations, t in 1..T) sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,t-1,1]  == 
  	 sum( m in moves : m.orig_x == l.x && m.orig_y == l.y) x[m,t,1] +
  	 sum(l1 in O :l1 == l ) q[l1,t];
  	
 //Flow conservation at nodes for blocking loads (commodity 2)
  forall ( l in locations, t in 1..T) sum( m in moves : m.dest_x == l.x && m.dest_y == l.y) x[m,t-1,2]  == 
  	 sum( m in moves : m.orig_x == l.x && m.orig_y == l.y) x[m,t,2];  	
  
  // Flow conservation at t= 0
  forall ( l in O ) supply[l,1] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,1] + q[l,0];
  
  forall ( l in locations diff O ) supply[l,1] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,1];
  
    
  forall ( l in locations) supply[l,2] == sum(m in moves: m.orig_x == l.x && m.orig_y == l.y) x[m,0,2];
   
  // Flow conservation at the sink
  sum(l in O, t in Tr) q[l,t] == card(R);
   
  // Generalized capacitiy constraint
  forall ( l in locations, t in 1..T )  
  	sum(i in 1..2,  m in moves : m.dest_x == l.x && m.dest_y == l.y ) x[m,t-1,i]  <= 1;

  // constraint - avoid conflicts
  if (MoveMethod == "LM") {
	forall ( l in locations, t in Tr )  
		sum(i in 1..2,  m in moves : m.dest_x == l.x && m.dest_y == l.y && (m.orig_x != l.x || m.orig_y != l.y )) x[m,t,i] 
		+ sum( l1 in O :l1 == l ) q[l1,t] 
		+ sum(i in 1..2,  m in moves : m.orig_x == l.x && m.orig_y == l.y && (m.dest_x != l.x || m.dest_y != l.y )) x[m,t,i] <= 1;
	
  } else {  // BM
		forall ( l in locations, t in Tr )  
			sum(i in 1..2, d in Dirs, m in moves: m.dest_x == l.x && m.dest_y == l.y && m.orig_x == l.x   && m.orig_y == l.y+d ) x[m,t,i] +
			sum(i in 1..2, d in Dirs, m in moves: m.orig_x == l.x && m.orig_y == l.y && m.dest_x == l.x+d && m.dest_y == l.y)    x[m,t,i] <= 1;
			
		forall ( l in locations, t in Tr )  
			sum(i in 1..2, d in Dirs, m in moves: m.dest_x == l.x && m.dest_y == l.y && m.orig_x == l.x+d && m.orig_y == l.y ) x[m,t,i] +
			sum(i in 1..2, d in Dirs, m in moves: m.orig_x == l.x && m.orig_y == l.y && m.dest_x == l.x && m.dest_y == l.y+d) x[m,t,i] <= 1;	
  
		// No swap - possible cut for LM and required in BM
		forall( m in moves, t in 0..T-1 : m.orig_x != m.dest_x || m.orig_y != m.dest_y) sum(i in 1..2) (x[m,t,i] + 
		x[<m.dest_x, m.dest_y, m.orig_x, m.orig_y>,t,i]) <= 1; 
  }  
  
  
   // ( stipulating z)
   if (alpha > 0)   forall( l in O,t in Tr)  t * q[l,t] <= z;
}


main {
	var max_t = 0;
	
    thisOplModel.generate();
    var success = cplex.solve()
    var f = new IloOplOutputFile("out_pbs2b.txt");
    if (success) {
		f.writeln("FlowTime=",thisOplModel.FlowTime);
		f.writeln("NumberOfMovements=",thisOplModel.NumberOfMovements);
		f.writeln("obj=",cplex.getObjValue());
	}  else {
		f.writeln("FlowTime=-1");
		f.writeln("NumberOfMovements=-1");
		f.writeln("obj=-1");
	}
	f.writeln("lb=",cplex.getBestObjValue());
	f.close()
	
	
	if (success) {
		for(t in thisOplModel.Tr) for (l in thisOplModel.O)  if (thisOplModel.q[l][t] == 1) {
			writeln("At time ",t," item retrived via O",l);
			if (t>max_t) max_t = t; 	
		}
 	
		if (thisOplModel.file_export != "") {
			var f = new IloOplOutputFile(file_export);
		  
			// Write the input and input in a format readable by our animation rutine.
		  
			f.writeln(thisOplModel.Lx,",", thisOplModel.Ly)
		  
			// B
			f.write("[");
			var lFirst = true
			for (l in thisOplModel.B ) {
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
			for (l in thisOplModel.R ) {
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
			for (l in thisOplModel.O ) {
				if (!lFirst) { 
					f.write(",");
					lFirst = false
				}     
				f.write("(", l.x,",", l.y,")");
			}  
			f.writeln("]");
			  
			  
			f.write("[")
			for(t=0 ; t<= max_t; t++) {
				f.write("[");
				var first = true;
				for (var  m in thisOplModel.moves) {
					if ((m.orig_x != m.dest_x  || m.orig_y != m.dest_y) && thisOplModel.x[m][t][1] +thisOplModel.x[m][t][2]  > 0.99) {
						if (first)
							first = false;
						else
							f.write(",")   
						f.write("((",m.orig_x, ",", m.orig_y,"),(", m.dest_x, ",",m.dest_y, "))"); 
					}      
				}
				
				for (l in thisOplModel.O) if( thisOplModel.q[l][t] > 0.99) {
				    if (first)
						first = false;
					else
						f.write(",")   
				    f.write("((",l.x, ",", l.y,"),(None, None))");
				}
				
				if (t < max_t)
					f.write("],");        
				else
					f.write("]]");
				
			}
		  
		    f.close();
		} // export  
	} //success
}