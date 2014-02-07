import java.util.*;
import java.awt.Rectangle;
import java.awt.Point;

public class Vehicle
{
	public Rectangle bounds;
	public Point loc;
	public String img;
	public int size;
	public int desVel;
	public int curVel;
		
	public Vehicle(Rectangle rect, Point location, String image, int totalSize, int desiredVelocity, int currentVelocity)
	{
		bounds = rect;
		loc = location;
		img = image;
		size = totalSize;
		desVel = desiredVelocity;
		curVel = currentVelocity;
	}
	
	public boolean HappyWithSpeed()
	{
		//TODO: Decide if we want a better function for this		
		return desVel == curVel;
	}
	
	@Override
	public String toString()
	{
		if(HappyWithSpeed())
		{
			return img.toUpperCase();
		}
		else
		{
			System.err.printf("Vehicle %s is not happy! desVel = %d, curVel = %d\n", img.toLowerCase(), desVel, curVel);
			return img.toLowerCase();
		}
	}
}