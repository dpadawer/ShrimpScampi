#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

# INTIALISATION
import pygame, math, sys
import random
from pygame.locals import *
screen = pygame.display.set_mode((1920, 760), FULLSCREEN)
clock = pygame.time.Clock()

TOTAL_LANES = 2
THRESHOLD = .1
LTORBIAS = .5
RTOLBIAS = -.75
XLIMIT = 1920
EPSILON = .01
DMG = 30
COMFORTBRAKE = 3
MINSPACE = 3
DTH = 1.5
LENGTH = 15
MAXACCEL = 2
SAFETYCRIT = 45
TIMEWARP = 1

addIdx = 0

#Since a car is 5 pixels wide, we will define a lane as 9 pixels
#Lane centers will start at y = 9 (then 18, 27, 36...)

class CarSprite(pygame.sprite.Sprite):
  def __init__(self, image, xposition, yposition, startVelocity, desiredVelocity, desiredMinGap, comfortableBraking, politeness, minSpace, desTimeHead, length, maxAcceleration, name):
    pygame.sprite.Sprite.__init__(self)
    self.src_image = pygame.image.load(image)
    #print(name, xposition, yposition)
    self.xpos = xposition
    self.ypos = yposition
    
    self.name = name
    
    self.curVel = startVelocity
    
    self.curAcc = 0
    
    self.desVel = desiredVelocity
    self.desMinGap = desiredMinGap
    
    self.length = length
    
    self.curLane = int(round(self.ypos / 9))
    self.targetLane = int(round(self.ypos / 9))
    
    self.maxAccel = maxAcceleration
    self.comfortBrake = comfortableBraking
    self.pol = politeness
    self.minSpacing = minSpace
    self.desTimeHeadway = desTimeHead
    
    
  def __repr__(self):
    return self.name + "={Pos: " + str((self.xpos, self.ypos)) + "; curVel, desVel: " + str((self.curVel, self.desVel)) + "; curLane, taretLane: " + str((self.curLane, self.targetLane)) + "}"
    
    
  #Problem: if we update acc, vel, and pos all in one pass, there is simultaneousness being removed
  #Hacky solution: 2 passes - first is update acc/vel, second is position
  #We claim this is valid (with regards to possesing a lane) since people (hopefully) use their blinker
  def update(self, deltat, carGroup, passNo):
    # SIMULATION
    print("Updating " + self.__repr__() + ". Pass " + str(passNo))
    
    #self.curLane = int(round((self.ypos - 5) / 9))
    
    if(self.ypos % 9 == 0):
      self.curLane = int(round((self.ypos % 150) / 9))
      #print("Set curLane of " + self.name + " to " + str(self.curLane) + ", target lane is " + str(self.targetLane))
      #self.targetLane = self.curLane
      
    if(self.xpos <= -200 or self.ypos >= 760 or self.ypos <= -200):
      carGroup.remove(self)
      return
      
    if(self.xpos >= XLIMIT):
      carGroup.remove(self)
      return
      '''
      self.xpos = self.xpos - XLIMIT
      self.ypos = self.ypos + 150
      '''
    
    if(passNo == 0):
      nears = self.findNears(carGroup)
      print(nears)
      
      
      accels = self.calcAccels(nears, carGroup)
      print(accels)

      which = accels.index(max(accels))
      print("Desired is " + str(which))
      
      if(which == 2 and self.isSafe(nears[4], nears[5], SAFETYCRIT)):
        #Merge right
        self.targetLane = self.curLane + 1
        self.curAcc = accels[2]
        print("Switching right")
      elif(which == 0 and self.isSafe(nears[0], nears[1], SAFETYCRIT)):
        #Merge left
        self.targetLane = self.curLane - 1
        self.curAcc = accels[0]
        print("Switching left")
      else:
        #Don't bother
        self.targetLane = self.curLane
        self.curAcc = accels[1]
        print("Staying put")
      
        
      self.curVel = self.curVel + self.curAcc
        
    else:      
      self.xpos = self.xpos + self.curVel
      #self.ypos = self.curLane * 9 + 5
      
      '''
      if(self.curLane > self.targetLane):
        self.ypos = self.ypos - 9
        self.curLane = self.targetLane
      elif(self.curLane < self.targetLane):
        self.ypos = self.ypos + 9
        self.curLane = self.targetLane
      '''
      
      if(self.curLane > self.targetLane):
        self.ypos = self.ypos - 3
        #self.curLane = self.targetLane
      elif(self.curLane < self.targetLane):
        self.ypos = self.ypos + 3
        #self.curLane = self.targetLane
      
      
      #print(self.name)
      self.rect = self.src_image.get_rect()
      #print(self.xpos, int(self.xpos))
      self.rect.centerx = int(self.xpos)
      #print(self.ypos, int(self.ypos))
      self.rect.centery = int(self.ypos)
      self.image = self.src_image
      
    '''
    print("Current lane: " + str(self.curLane))
    print("Target lane: " + str(self.targetLane))
    #print(self.xpos, self.ypos)
    print(self.curVel, self.desVel)
    '''
    
    print("Finished updating " + self.__repr__())
    if(self.curVel < 0):
      sys.exit(0)
    
    if(math.fabs(self.curVel) > 1000000):
      carGroup.remove(self)
    
  def findNears(self, carGroup):
    #We now want a list with 6 elements: nearestAheadLeft, nearestBehindLeft, nearestAheadSame, nearestBehindSame, nearestAheadRight, nearestBehindRight
    #We define "ahead" as ypos >= to ours,
    # behind as ypos < ours
    # (So we don't get a car marked as both ahead of and behind us)
    #TODO: Is that actually appropraite/acceptable/correct?
    dists = [sys.maxint for x in range(6)]
    nears = [None for x in range(6)]
    
    #Might be able to do this some clever way, but this is (fairly) simple, albeit ugly
    for car in carGroup:
      if(car == self): continue
      dist = math.fabs(car.xpos - self.xpos)
      if(car.curLane == self.curLane - 1 or car.targetLane == self.curLane - 1):
        if(car.xpos >= self.xpos):
          if(dist < dists[0]):
            nears[0] = car
            dists[0] = dist
        else:
          if(dist < dists[1]):
            nears[1] = car
            dists[1] = dist
      elif(car.curLane == self.curLane or car.targetLane == self.curLane):
        if(car.xpos >= self.xpos):
          if(dist < dists[2]):
            nears[2] = car
            dists[2] = dist
        else:
          if(dist < dists[3]):
            nears[3] = car
            dists[3] = dist
      elif(car.curLane == self.curLane + 1 or car.targetLane == self.curLane + 1):
        if(car.xpos >= self.xpos):
          if(dist < dists[4]):
            nears[4] = car
            dists[4] = dist
        else:
          if(dist < dists[5]):
            nears[5] = car
            dists[5] = dist
    
    '''
    if(nears[0] != None): print ("Returning left: " + nears[0].name)
    else: print("None on left")
    if(nears[2] != None): print ("Returning center: " + nears[2].name)
    else: print("None on center")
    if(nears[4] != None): print ("Returning right: " + nears[4].name)
    else: print("None on right")
    '''
    
    return nears
    
  def calcAccels(self, nears, carGroup):
    accels = [0 for x in range(3)]
    
    if(self.curLane == 0):
      accels[0] = -sys.maxint
    else:
      if(nears[0] == None):
        accels[0] = self.calcAccelFree()
      else:
        accels[0] = self.calcAccelInt(nears[0], carGroup)
      
    if(nears[2] == None):
      accels[1] = self.calcAccelFree()
    else:
      accels[1] = self.calcAccelInt(nears[2], carGroup);
    
    if(self.curLane == TOTAL_LANES - 1):
      accels[2] = -sys.maxint
    else:
      if(nears[4] == None):
        accels[2] = self.calcAccelFree()
      else:
        accels[2] = self.calcAccelInt(nears[4], carGroup);
      
    return accels
    
  def calcAccelFree(self):
    #print("calcAccelFree Returning " + str(self.maxAccel * (1 - ((self.curVel / self.desVel) ** 4))))
    return self.maxAccel * (1 - ((self.curVel / self.desVel) ** 4))
  
  def calcAccelInt(self, near, carGroup):      
    #print("self: " + self.__repr__())
    #print("near: " + near.__repr__())
      
    #delvalpha = self.curVel - near.curVel
    delvalpha = near.curVel - self.curVel
    if(math.fabs(delvalpha) > 250):
      print("dangerous delvalpha found: self: " + self.__repr__() + "; near: " + near.__repr__())
    #print("self.curVel: " + str(self.curVel) + ", near.curVel: " + str(near.curVel))
    
    #sstar = self.minSpacing + (self.curVel * self.desTimeHeadway) + ((self.curVel * delvalpha) / (2 * math.sqrt(self.maxAccel * self.comfortBrake)));
    #print("self: " + str(self.curVel) + " near: " + str(near.curVel) + " " + near.name)
    #print ("delvalpha :" + str(delvalpha))
    sstar = self.minSpacing + (self.curVel * self.desTimeHeadway) * math.exp((delvalpha) / (2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfortBrake)))
    salpha = near.xpos - self.xpos - near.length
      
    if(salpha == 0):
      print("calcAccelInt Returning -sys.maxint")
      return -sys.maxint
    
    freeAccel = self.calcAccelFree()
    
    #print("calcAccelInt Returning " + str(-self.maxAccel * ((sstar / salpha) ** 2)))
    return self.maxAccel * (freeAccel - ((sstar / salpha) ** 2))
    
  #TODO: Potentially set different safety criteria for ahead and behind
  def isSafe(self, aheadCar, behindCar, safetyCrit):
    #print("In isSafe with " + self.name)
    forwardVal = 0
    behindVal = 0
    if(aheadCar == None):
      forwardVal = sys.maxint
    else:
      forwardVal = math.fabs(aheadCar.xpos - self.xpos)
    
    if(behindCar == None):
      behindVal = sys.maxint
    else:
      behindVal = math.fabs(behindCar.xpos - self.xpos)
      
    if(forwardVal > safetyCrit and behindVal > safetyCrit):
      #print("Returning true")
      return True
    
    #print("Returning false")
    return False
    
      
  
# Make a couple of cars
#img, xPos, yPos, startVel, desVel, DMG, comfortBrake, politeness, minSpace, DTH, l, maxAcc):

#car1 = CarSprite('car1.png', 50, 23, 30, 35, 10, 3, 1, 5, 1.5, 10, 1, "Car1") #Red
#car2 = CarSprite('car2.png', 100, 23, 24, 35, 10, 3, 1, 5, 1.5, 10, 1, "Car2") #Blue
#car3 = CarSprite('car3.png', 150, 23, 21, 25, 10, 3, 1, 5, 1.5, 10, 1, "Car3") #Green


'''
car1 = CarSprite('car1.png', 50, 14, 25, 60, 2, 3, 1, 5, 1.5, 1, 1, "Car1") #Red
car2 = CarSprite('car2.png', 100, 14, 25, 30, 2, 3, 1, 5, 1.5, 1, 1, "Car2") #Blue
car3 = CarSprite('car3.png', 150, 14, 25, 30, 2, 3, 1, 5, 1.5, 1, 1, "Car3") #Green


#cars = [car1]
'''


#cars = [car1, car2, car3]


'''
for i in range(10):
  car = CarSprite('car' + str(random.randint(1,3)) + ".png", 50 * i + 50, 9, random.randint(25, 45), random.randint(25, 45), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(i))
  print("Created " + car.name + " with speed " + str(car.curVel))
  cars.append(car)
'''

cars = []
car_group = pygame.sprite.RenderPlain(*cars);

while 1:
  # USER INPUT
  deltat = clock.tick(30)
  
  
  if(addIdx % 4 == 0 and len(cars) < 1000):
    startVel = random.randint(35, 45) / TIMEWARP
    car = CarSprite('car' + str(random.randint(1,3)) + ".png", random.randrange(25, 75, 25), random.randrange(9, 9 * TOTAL_LANES, 9), startVel, startVel + (random.randint(-3, 3) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
    cars.append(car)
    car_group = pygame.sprite.RenderPlain(*cars)
  
  addIdx = addIdx + 1
  
  
  print("TICK")
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  # RENDERING
  
  screen.fill((0,0,0))
  car_group.update(deltat, car_group, 0)
  print("TOCK")
  car_group.update(deltat, car_group, 1)
  car_group.draw(screen)
  pygame.display.flip()
  print("")

