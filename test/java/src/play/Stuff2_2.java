package play;

public class Stuff2_2 extends Stuff2 {

	public Stuff2_2() {
		// TODO Auto-generated constructor stub
	}

	
	void printStatus () {
		System.out.println(this.getClass().getName() + this.getClass().getMethods().toString());
		
	}
	
	void printRes() {
		System.out.println(this.getClass().getName() + this.getClass().getMethods());

	}
	
	void printType() {
		System.out.println(this.getClass().getName() + this.getClass().getMethods());

	}
	
	
	
}
