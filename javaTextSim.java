import java.util.*;
import java.awt.Rectangle;
import java.awt.Point;

public class javaTextSim
{
	public static int NO_LANES = 2;
	public static int LANE_LENGTH = 30;
	public static int SIM_LENGTH = 1000;
	//I'm a bad person. Global variables.
	public static char[][] road = new char[NO_LANES][LANE_LENGTH];
	public static ArrayList<Vehicle> vehicles = new ArrayList<Vehicle>();
	
	public static void main(String[] args)
	{			
		///[LANE#][LANEPOS]
		Vehicle v1 = new Vehicle(new Rectangle(0, 0, 1, 1), new Point(1, 0), "A", 1, 2, 1);
		Vehicle v2 = new Vehicle(new Rectangle(0, 0, 1, 1), new Point(1, 1), "W", 1, 1, 1);
		
		vehicles.add(v1);
		vehicles.add(v2);
		
		int curTime = 0;
		while(curTime < SIM_LENGTH)
		{
			System.out.printf("Time: %d\n", curTime);
			
			ClearRoad();
			System.err.println("Cleared road");
			Update(vehicles);
			DrawRoad(true);
			
			curTime++;
			System.out.printf("End t = %d\n", curTime);
		}
	}
	
	public static void Update(ArrayList<Vehicle> vehicles)
	{
		ArrayList<Vehicle> toRemove = new ArrayList<Vehicle>();
	
		for(Vehicle vehicle : vehicles)
		{
			///Check for collisions
			for(Vehicle other : vehicles)
			{
				if(other.equals(vehicle))
				{
					continue;
				}
				
				if(other.loc.equals(vehicle.loc))
				{
					//Oops. Bad juju.
					//TODO: decide how to handle
				}
			}

			///Update state
			//Are we in the rightmost lane?
			if(vehicle.loc.y == NO_LANES - 1)
			{
				if(vehicle.HappyWithSpeed())
				{
					//Do nothing, in terms of changing lanes
				}
				else
				{
					//Don't drive on the shoulder.
					if(vehicle.loc.x != 0 && CanJoinLane(vehicle, vehicle.loc.x, vehicle.loc.x - 1))
					{
						vehicle.loc.x--;
					}
				}
			}
			else
			{
				//TODO: Merge back if safe.
				if(CanJoinLane(vehicle, vehicle.loc.x, vehicle.loc.x + 1))
				{
					vehicle.loc.x++;
				}
				else
				{
					//Stay here for now.
				}
			}
			
			///Update in-lane location
			//TODO: Make sure our current velocity doesn't collide us with anyone.
			// If it does, don't go at that velocity!
			vehicle.loc.y += vehicle.curVel;
			
			
			//If this takes us off the road, remove us from the list. We've left the simulation.
			if(vehicle.loc.y >= LANE_LENGTH)
			{
				toRemove.add(vehicle);
			}
			else
			{
				//TODO: account for multiple length vehicles
				road[vehicle.loc.x][vehicle.loc.y] = vehicle.img.charAt(0);
				System.err.printf("Added vehicle %c at %d, %d\n", vehicle.img.charAt(0), vehicle.loc.x, vehicle.loc.y);
			}
		}
		
		///Remove anyone who left the simulation.
		for(Vehicle vehicle : toRemove)
		{
			vehicles.remove(vehicle);
		}
	}
	
	//Check for any cars within toCheck in laneNo.
	//This will be used both for our current speed and for merging.
	public static ArrayList<Vehicle> nAhead(Vehicle fromMe, int toCheck, int laneNo)
	{
		ArrayList<Vehicle> toReturn = new ArrayList<Vehicle>();
	
		//Check for vehicles in my lane within toCheck of fromMe.
		for(Vehicle vehicle : vehicles)
		{
			if(vehicle.equals(fromMe))
			{
				continue;
			}
			
			//Don't update for their speed - we should set this up such that we work front of the line back.
			// That is, they've already moved this step.
			if(vehicle.loc.x == laneNo && vehicle.loc.y > fromMe.loc.y && vehicle.loc.y <= fromMe.loc.y + toCheck)
			{
				toReturn.add(vehicle);
			}
		}
		
		return toReturn;
	}
	
	//We can if we are safe for the whole of our travel by curVel ahead and in that lane.
	//TODO: Need to check backwards?
	public static boolean CanJoinLane(Vehicle who, int curLane, int targetLane)
	{
		return nAhead(who, who.curVel, curLane).isEmpty() && nAhead(who, who.curVel, targetLane).isEmpty();
	}
	
	public static void ClearRoad()
	{
		for(int i = 0; i < NO_LANES; i++)
		{
			for(int j = 0; j < LANE_LENGTH; j++)
			{
				road[i][j] = ' ';
			}
		}
	}
	
	public static void DrawRoad(boolean drawLanes)
	{
		if(drawLanes)
		{
			for(int j = 0; j < LANE_LENGTH; j++)
			{
				System.out.print('-');
			}
			System.out.print("\n");
		}
	
		for(int i = 0; i < NO_LANES; i++)
		{
			for(int j = 0; j < LANE_LENGTH; j++)
			{
				System.out.print(road[i][j]);
			}
			System.out.print("\n");
			
			if(drawLanes)
			{
				for(int j = 0; j < LANE_LENGTH; j++)
				{
					System.out.print('-');
				}
				System.out.print("\n");
			}
		}
	}
}