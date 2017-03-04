package play;
import java.util.*;
import java.util.ArrayList;

public class Stuff1 {

	ArrayList<StuffContainer> SAL_global = null;
	
	Stuff1() {
	    ArrayList<StuffContainer> stuffsArrayList = new ArrayList<StuffContainer>();
		System.out.println("stuffs");
		 String[] stuffstype = {"a","b","c","d"};
		 String[] stuffsitems = {"1","2","3","4","5","6","7","8","9","10","11","12","13","14","15"}; 
		 
		 for (int i=0;i<stuffstype.length ; i++ ) {
			 for (int j=0 ; j<stuffsitems.length ; j++ ) {
				 StuffContainer StuffContainer = new StuffContainer() ;
				 StuffContainer.setstufftype(stuffstype[i]);
				 StuffContainer.setstuffitem(stuffsitems[j]);
				 stuffsArrayList.add(StuffContainer);
				 //System.out.print(i+"/"+j + ":"+stuff.getstufftype() + stuff.getstuffitem());
				 //System.out.println();
			 }
		 }
		 this.SAL_global = stuffsArrayList;
		return ;
	}

	void printStuffsArrayList(ArrayList<StuffContainer>  SAL){
		int i=0;
		for (StuffContainer o : SAL) {
			System.out.print(i +":"+ o.getstufftype() + o.getstuffitem() );
			System.out.println();
			i++;
		}
		
	}
	
	ArrayList<StuffContainer> mixStuff(ArrayList<StuffContainer> SAL) {
		
		ArrayList<StuffContainer> mixArrayStuffArray  = new ArrayList<StuffContainer>() ;
		HashMap<String,String> verifyMap = new HashMap<String,String>(); 
		
		int safeCount =0;
		int sal_size = SAL.size();
		int orig_sal_size = sal_size;
		String key_verify_hash_map ="";
		
		try {
		
			while (SAL.size() >0 && safeCount++ <orig_sal_size)  {
				sal_size = SAL.size();
				
				Random rn = new Random() ;
				int rem_rand_entry_nbr=rn.nextInt(sal_size);
				mixArrayStuffArray.add(SAL.get(rem_rand_entry_nbr)) ;
				key_verify_hash_map=SAL.get(rem_rand_entry_nbr).getstufftype()+SAL.get(rem_rand_entry_nbr).getstuffitem();
				System.out.println("remove " + rem_rand_entry_nbr + "  Size=" + sal_size + "key=" + key_verify_hash_map);
				if (verifyMap.containsKey(key_verify_hash_map)) {
					throw new Exception("Was deleted before !!!") ;
				} else {
					verifyMap.put(key_verify_hash_map, key_verify_hash_map);
				}
				SAL.remove(rem_rand_entry_nbr);
				rn=null;
				
				
			}
			
			if (safeCount > orig_sal_size) {
				System.out.println("Safe count exceeded !!!");
				System.exit(-1);
			}
		} 

		catch (Throwable e) {
			e.printStackTrace();
			System.exit(-1);
		}
			
		return mixArrayStuffArray;
		
	}
	
	
	
	
	 public static void main(String args[]) {
		 Stuff1 stuff = new Stuff1();
		 stuff.printStuffsArrayList(stuff.SAL_global);
		 System.out.println("*******************************************************************");
		 ArrayList<StuffContainer> SAL_mix = stuff.mixStuff(stuff.SAL_global);
		 stuff.printStuffsArrayList(stuff.SAL_global);
		 System.out.println("---------------------------------------------------------------------");
		 stuff.printStuffsArrayList(SAL_mix);

		 
	 }
	 
	 
	 
	 
	 public static class StuffContainer {
		String cartype = null;
		String stuffitem = null;

		StuffContainer () {
			 
		}
		 
		public String getstufftype() {
			return cartype;
		}
		public void setstufftype(String cartype) {
			this.cartype = cartype;
		}
		public String getstuffitem() {
			return stuffitem;
		}
		public void setstuffitem(String stuffitem) {
			this.stuffitem = stuffitem;
		}
		 
		 
		 
	 }


}
