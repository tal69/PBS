/*********************************************
 * OPL 12.10.0.0 Model
 * Author: talra
 * Creation Date: Sep 20, 2020 at 11:52:49 PM
 *********************************************/

 int num_sets = ...;
 
 tuple pair {
   int x;
   int y;
 }
 
 range sets_range = 0..(num_sets-1);
 
 float v[sets_range] = ...;
 {pair} E[sets_range] = ...;
 {pair} L = ...;
 
 dvar boolean x[sets_range];
 
 maximize sum(i in sets_range) v[i]*x[i];
 subject to {
   forall (j in L) sum(i in sets_range : j in E[i] ) x[i] <= 1;
 }
 
 execute {  
   var f = new IloOplOutputFile("SetPacking.txt");
   var lFirst = true;
   f.write("[");
   for (var i in sets_range) {
     	if (x[i] > 0.99) {
       		if (lFirst) lFirst= false; else f.write(",");
       		f.write(i);	
   		}     
   }
   f.write("]");
}