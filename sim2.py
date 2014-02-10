#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

#INITIALISATION
DISPLAYWIDTH = 1800

import pygame, math, sys, random
from pygame.locals import *
screen = pygame.display.set_mode((DISPLAYWIDTH, 700))
clock = pygame.time.Clock()

#Road stuff
LANEWIDTH = 9
UPPERBUF = 9

TOTALLANES = 5
XLIMIT = 50000

#Merging stuff
THRESHOLD = .1
LTORBIAS = 10
RTOLBIAS = 0

#Spawn stuff
SPAWNPERCENT = 1
BASESPEED = 0
SPEEDVAR = 20

#Values from papers
#Note: Length is 12 for display purposes, thus all other distance constants is also multiplied by 3
#These values specifically from http://www.itrn.ie/uploads/sesc3_id153.pdf
COMFBRAKE = 6
POLITENESS = 1
MINSPACE = 6
DESTIMEHEADWAY = 1.2
LENGTH = 12
HEIGHT = 6
MAXACC = 4.5
SAFETYCRIT = LENGTH * 4

#COLORS
GREEN = ((0, 255, 0))
RED = ((255, 0, 0))
BLUE = ((0, 0, 255))
BLACK = ((0, 0, 0))
WHITE = ((255, 255, 255))
GRAY = ((125, 125, 125))

MergeCount = 0
CollisionCount = 0

#HELPER FUNCTIONS
def GetLane(ypos):
  return ((ypos - UPPERBUF) / LANEWIDTH) - 1
  
def GetYForLane(laneNo):
  return ((laneNo + 1) * LANEWIDTH) + UPPERBUF
  
def CompletelyInLane(ypos):
  return (ypos - UPPERBUF) % LANEWIDTH == 0
  
def DrawLanes(offset):
  pygame.draw.line(screen, WHITE, [0, UPPERBUF + offset], [DISPLAYWIDTH, UPPERBUF + offset], 1)
  for i in range(1, TOTALLANES):
    pygame.draw.line(screen, GRAY, [0, LANEWIDTH * i + UPPERBUF + offset], [DISPLAYWIDTH, LANEWIDTH * i + UPPERBUF + offset], 1)
  pygame.draw.line(screen, WHITE, [0, LANEWIDTH * TOTALLANES + UPPERBUF + offset], [DISPLAYWIDTH, LANEWIDTH * TOTALLANES + UPPERBUF + offset], 1)

#GAME CLASSES
class CarSprite(pygame.sprite.Sprite):
  def __init__(self, xposition, yposition, startVelocity, desiredVelocity, comfortableBraking, politeness, minimumSpacing, desiredTimeHeadway, length, height, maximumAcceleration, safetyCriteria, name):
    pygame.sprite.Sprite.__init__(self)
    self.xpos = xposition
    self.ypos = yposition
    self.curVel = startVelocity
    self.desVel = desiredVelocity
    self.curAccel = 0
    
    self.maxAccel = maximumAcceleration
    self.comfBrake = comfortableBraking
    self.minSpace = minimumSpacing
    self.desTimeHeadway = desiredTimeHeadway

    self.length = length
    self.height = height
    
    self.curLane = GetLane(yposition)
    self.targetLane = self.curLane
    
    self.passing = False
    self.colliding = False
    self.name = name
    
    self.politeness = politeness
    self.safetyCrit = safetyCriteria
    
    self.rect = pygame.Rect(self.xpos, self.ypos, length, height)
    self.color = GREEN
    
  def __repr__(self):
    return str((self.name, self.xpos, self.ypos, self.curVel, self.desVel, self.curAccel, self.curLane, self.targetLane))
    
  def update(self, carGroup):
    if(self.name == "dummy"): return
    #Update accel, then vel, the pos
    #print("Updating " + self.__repr__())
    
    if(self.xpos < -100 or self.xpos > XLIMIT):
      #print(self.__repr__())
      carGroup.remove(self)
      self.rect = pygame.Rect(0, 0, 0, 0)
      self = None
      return
    
    #Can only change lanes if not already mid-change
    nears = self.calcNears(carGroup)
    #print(nears)
    myAccels = [0 for x in range(3)]
    rearAccels = [0 for x in range(3)]
    rearNewAccels = [0 for x in range(3)]
    accelUtilities = [0 for x in range(3)]
    
    #Where I can go
    myAccels[1] = self.calcAccel(nears[2])
    if(not self.passing):
      myAccels[0] = self.calcAccel(nears[0])# if self.curLane > 0 else 0
      myAccels[2] = self.calcAccel(nears[4])# if self.curLane < TOTALLANES else 0
      
      #Their accelerations assuming I'm there
      rearAccels[0] = nears[1].calcAccel(self)
      rearAccels[1] = nears[3].calcAccel(self)
      rearAccels[2] = nears[5].calcAccel(self)
      
      #Their accelerations assuming I leave
      rearNewAccels[0] = nears[1].calcAccel(nears[0])
      rearNewAccels[1] = nears[3].calcAccel(nears[2])
      rearNewAccels[2] = nears[5].calcAccel(nears[4])
      
      #Let's calculate them
      accelUtilities = [0 for x in range(3)]
      accelUtilities[0] = myAccels[0] - self.politeness * (rearAccels[0] + rearNewAccels[1]) + RTOLBIAS
      accelUtilities[1] = myAccels[1]
      accelUtilities[2] = myAccels[2] - self.politeness * (rearAccels[2] + rearNewAccels[1]) + LTORBIAS
      
      '''
      print(self.name + " accels:")
      print(myAccels)
      print("rearAccels:")
      print(rearAccels)
      print("rearNewAccels:")
      print(rearNewAccels)
      print("accel utilities")
      print(accelUtilities)
      '''
      
      together = zip(accelUtilities, [0,1,2])
      sortedTogether = sorted(together)
      
      sortedOrder = [x[1] for x in reversed(sortedTogether)]
      
      #print(sortedOrder)

      #if(nears[0].passing or nears[1].passing or nears[2].passing or nears[3].passing or nears[4].passing or nears[5].passing):
      #if(nears[1].passing or nears[3].passing or nears[5].passing):
        #x = [1]
      
      for x in sortedOrder:
        #Check if we can make the merge. If we can, do it and exit the loop
        #Otherwise, keep looking
        if(x == 2):
          if(accelUtilities[2] >= THRESHOLD and self.isSafe(nears[4], nears[5]) and self.curLane < TOTALLANES - 1):
            #Merge right
            self.curAccel = myAccels[2]
            whichLane = 2
            self.targetLane = self.curLane + 1
            self.passing = True
            #print("Choosing right")
            break
        elif(x == 0):
          if(accelUtilities[0] >= THRESHOLD and self.isSafe(nears[0], nears[1]) and self.curLane > 0):
            #Merge left
            self.curAccel = myAccels[0]
            self.targetLane = self.curLane - 1
            whichLane = 0
            self.passing = True
            #print("Choosing left")
            break;
        else:
          #Stay here
          self.curAccel = myAccels[1]
          #print("Staying put")
          break
          
    else:
      self.curAccel = myAccels[1]

    
    if(self.passing):
      if(self.curLane > self.targetLane):
        self.ypos -= 3
      else:
        self.ypos += 3
      
      if(GetLane(self.ypos) == self.targetLane and CompletelyInLane(self.ypos)):
        self.curLane = self.targetLane
        self.passing = False
        global MergeCount
        MergeCount += 1
    
    self.curVel += self.curAccel
    self.xpos += self.curVel
    #Check for crashes
    collisions = pygame.sprite.spritecollide(self, carGroup, False)
    if(len(collisions) > 1):
      self.color = RED
      global CollisionCount
      CollisionCount += 1
      #print(self.__repr__())
      self.rect = pygame.Rect(0, 0, 0, 0)
      self.xpos = XLIMIT + 5
      self.ypos = 1000
      self = None
      return
    else:
      tmp = (math.fabs(self.curVel - self.desVel) / self.desVel)
      self.color = ((0, min(max(255 - int(255 * tmp), 0), 255), min(max(0, int(255 * tmp)), 255)))
    
    #print("Finished updating " + self.__repr__())
    
    #Draw
    if(self.curVel < 0 or self.xpos < -100 or self.xpos > XLIMIT):
      #print(self.__repr__())
      self = None
      return
    #print((self.xpos, self.ypos, self.length, self.height))
    self.rect = pygame.Rect(round(self.xpos), round(self.ypos), self.length, self.height)
    pygame.draw.rect(screen, self.color, self.rect)
    
  def calcAccel(self, ahead):
    if(self.name == "dummy" or ahead == None):
      return 0
    vav0d = (self.curVel / self.desVel) ** 4
    #print("vav0d: " + str(vav0d))
    
    sStarTerm1 = self.minSpace
    sStarTerm2 = self.curVel * self.desTimeHeadway
    sStarTerm3Num = self.curVel - ahead.curVel
    sStarTerm3Denom = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
    sStarTerm3 = sStarTerm3Num / sStarTerm3Denom
    
    if(sStarTerm3 >= 50):
      return self.maxAccel
    
    sAlpha = ahead.xpos - self.xpos - ahead.length
    if(sAlpha == 0):
      #Results in a crash. lim -> -oo, so we're returning a really negative number
      return -100000
    
    sStar = sStarTerm1 + sStarTerm2 * math.exp(sStarTerm3)
    finalTerm = (sStar / sAlpha) ** 2
    #print("sStar / sAlpha squared: " + str(finalTerm))
    
    calcedAccel = self.maxAccel * (1 - vav0d - finalTerm)
    #print("Returning " + str(calcedAccel))
    return calcedAccel

  def calcNears(self, carGroup):
    #print("calcNears for " + self.__repr__())
    dists = [sys.maxint for x in range(6)]
    nears = [None for x in range(6)]
    for car in carGroup:
      if(car == self): continue
      curDist = math.fabs(self.xpos - car.xpos)
      #print("Looking at car " + car.__repr__())
      #Everybody loook left
      if(car.curLane == self.curLane - 1 or car.targetLane == self.curLane - 1):
        if(car.xpos >= self.xpos and curDist < dists[0]):
          dists[0] = curDist
          nears[0] = car
        elif(car.xpos <= self.xpos and curDist < dists[1]):
          dists[1] = curDist
          nears[1] = car
      #Everybody loooook right
      elif(car.curLane == self.curLane + 1 or car.targetLane == self.curLane + 1):
        if(car.xpos >= self.xpos and curDist < dists[4]):
          dists[4] = curDist
          nears[4] = car
        elif(car.xpos <= self.xpos and curDist < dists[5]):
          dists[5] = curDist
          nears[5] = car
      #Everywhere you look...
      elif(car.curLane == self.curLane or car.targetLane == self.curLane):
        if(car.xpos >= self.xpos and curDist < dists[2]):
          dists[2] = curDist
          nears[2] = car
        elif(car.xpos <= self.xpos and curDist < dists[3]):
          dists[3] = curDist
          nears[3] = car
    
    #print("calcNears returning " + str(nears))
    return nears

  def isSafe(self, ahead, behind):
    if(ahead == None and behind == None):
      return True
    elif(ahead == None):
      return self.xpos - behind.xpos >= self.safetyCrit
    elif(behind == None):
      return ahead.xpos - self.xpos >= self.safetyCrit
    else:  
      return ((ahead.xpos - self.xpos >= self.safetyCrit) and (self.xpos - behind.xpos >= self.safetyCrit))
    
  def oldisSafe(self, ahead, behind):
    #print("new set")
    #print("In is safe for " + self.__repr__())
    #print("Ahead: " + ahead.name + "; behind: " + behind.name)
    #print(ahead.__repr__())
    #Check ahead
    if(ahead != None):
      sStarTerm1A = self.minSpace
      sStarTerm2A = self.curVel * self.desTimeHeadway
      sStarTerm3NumA = self.curVel - ahead.curVel
      sStarTerm3DenomA = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
      sStarTerm3A = sStarTerm3NumA / sStarTerm3DenomA
      
      if(sStarTerm3A >= 50):
        return True
      
      sStarA = sStarTerm1A + sStarTerm2A * math.exp(sStarTerm3A)
      
      if(sStarA < self.safetyCrit):
        return false;
      #print("sStarA: " + str(sStarA))
    
    if(behind != None):
      #Check behind
      sStarTerm1B = self.minSpace
      #print(sStarTerm1B)
      sStarTerm2B = self.curVel * self.desTimeHeadway
      #print(sStarTerm2B)
      sStarTerm3NumB = self.curVel - behind.curVel
      sStarTerm3DenomB = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
      sStarTerm3B = sStarTerm3NumB / sStarTerm3DenomB
      #print(sStarTerm3B)
      
      if(sStarTerm3B >= 50):
        return True
      
      sStarB = sStarTerm1B + sStarTerm2B * math.exp(sStarTerm3B)
      #print("sStarB: " + str(sStarB))
      
      if(sStarB < self.safetyCrit):
        return false;
    
    #if((sStarA >= self.safetyCrit * self.curVel or ahead.name == "dummy") and (sStarB >= self.safetyCrit * self.curVel or behind.name == "dummy")):
    return True
      
#START UP SPRITES
#self, x, y, startVel, desVel, comfBrake, p, minSpace, desiredTime, length, height, maxAcc, safetyCrit, name):
#car1 = CarSprite(50, GetYForLane(1), 10, 120, 2, .5, 2, 1.2, 4, 2, 1.5, 25, "car1")
#truck1 = CarSprite(225, GetYForLane(1), 35, 40, 2, 0, 2, 1.2, 12, 6, 1.5, 25, "truck1")
#truck2 = CarSprite(125, GetYForLane(1), 35, 45, 2, 0, 2, 1.2, 12, 6, 1.5, 25, "truck2")
#truck3 = CarSprite(25, GetYForLane(1), 35, 50, 2, 0, 2, 1.2, 12, 6, 1.5, 25, "truck3")
#cars = [car1, truck1]
#cars = [truck1, truck2, truck3]

cars = []

#Add dummy cars beyond infinity, so we can avoid ugly cases in calcAccel
for i in range(-1, TOTALLANES + 2):
  endDummyCar = CarSprite(sys.maxint, GetYForLane(i), 120, 120, 1, 1, 1, 1, 1, 1, 1, 1, "dummy")
  cars.append(endDummyCar)
  startDummyCar = CarSprite(-(sys.maxint / 2), GetYForLane(i), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "dummy")
  cars.append(startDummyCar)

carGroup = pygame.sprite.RenderPlain(*cars)
  
curTime = 0
totalSpawned = 0

    
#GAME LOOP
while 1:  
  #USER INPUT
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  
  #UPDATE STUFF
  #Draw the background
  screen.fill(BLACK)
  DrawLanes(7)
  #Add any new cars
  if(curTime % 5 == 0):
    for i in range(0, TOTALLANES):
      vel = random.randrange(BASESPEED, BASESPEED + SPEEDVAR)
      newCar = CarSprite(25, GetYForLane(i), 0, vel + random.randrange(5, SPEEDVAR), COMFBRAKE, POLITENESS, MINSPACE, DESTIMEHEADWAY, LENGTH, HEIGHT, MAXACC, SAFETYCRIT, "car" + str(totalSpawned))
      nears = newCar.calcNears(carGroup)
      # and newCar.isSafe(nears[2], nears[3])
      if(random.random() <= SPAWNPERCENT):
        cars.append(newCar)
        totalSpawned += 1
  
  #Update cars appropriately
  carGroup = pygame.sprite.RenderPlain(*cars)
  carGroup.update(carGroup)
  
  if(curTime % 25 == 0):
    print("Time: " + str(curTime) + ", merges: " + str(MergeCount) + ", collisions: " + str(CollisionCount))
  
  clock.tick(10)
  curTime += 1
  pygame.display.flip()
  
  #print("\n")