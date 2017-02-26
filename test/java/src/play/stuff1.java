package play;
import java.util.*;
import java.util.ArrayList;

public class stuff1 {
	

	 public static void main(String args[]) {

		 System.out.println("stuffs");
		 String[] stuffstype = {"a","b","c","d"};
		 String[] stuffsitems = {"1","2","3","4","5","6","7","8","9","10","V","Q","K","J"}; 
		 ArrayList<Object> stuffsArrayList = new ArrayList<Object>();
		 
		 for (int i=0;i<stuffstype.length ; i++ ) {
			 for (int j=0 ; j<stuffsitems.length ; j++ ) {
				 stuff stuff = new stuff() ;
				 stuff.setCartype(stuffstype[i]);
				 stuff.setstuffitem(stuffsitems[j]);
				 stuffsArrayList.add(stuff);
				 System.out.println(stuff.toString());
			 }
		 }
		 
		}
	 
	 
	 public static class stuff {
		String cartype = null;
		String stuffitem = null;

		stuff () {
			 
		}
		 
		public String getCartype() {
			return cartype;
		}
		public void setCartype(String cartype) {
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
