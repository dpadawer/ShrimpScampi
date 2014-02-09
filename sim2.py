#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

#INITIALISATION
import pygame, math, sys, random
from pygame.locals import *
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

LANEWIDTH = 9
UPPERBUF = 9

TOTALLANES = 2
XLIMIT = 5000

THRESHOLD = .1
LTORBIAS = .1
RTOLBIAS = -.1

#COLORS
GREEN = ((0, 255, 0))
RED = ((255, 0, 0))
BLUE = ((0, 0, 255))
BLACK = ((0, 0, 0))
WHITE = ((255, 255, 255))
GRAY = ((125, 125, 125))

#HELPER FUNCTIONS
def GetLane(ypos):
  return ((ypos - UPPERBUF) / LANEWIDTH)
  
def GetYForLane(laneNo):
  return (laneNo * LANEWIDTH) + UPPERBUF
  
def DrawLanes(offset):
  pygame.draw.line(screen, WHITE, [0, UPPERBUF + offset], [800, UPPERBUF + offset], 1)
  for i in range(1, TOTALLANES):
    pygame.draw.line(screen, GRAY, [0, (LANEWIDTH + 1) * i + UPPERBUF + offset], [800, (LANEWIDTH + 1) * i + UPPERBUF + offset], 1)
  pygame.draw.line(screen, WHITE, [0, (LANEWIDTH + 1) * TOTALLANES + UPPERBUF + offset], [800, (LANEWIDTH + 1) * TOTALLANES + UPPERBUF + offset], 1)

#GAME CLASSES
class CarSprite(pygame.sprite.Sprite):
  def __init__(self, xposition, yposition, startVelocity, desiredVelocity, desiredMinGap, comfortableBraking, politeness, minimumSpacing, desiredTimeHeadway, length, height, maximumAcceleration, safetyCriteria, name):
    pygame.sprite.Sprite.__init__(self)
    self.xpos = xposition
    self.ypos = yposition
    self.curVel = startVelocity
    self.desVel = desiredVelocity
    self.curAccel = 0
    
    self.desMinGap = desiredMinGap
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
    
    #Can only change lanes if not already mid-change
    nears = self.calcNears(carGroup)
    myAccels = [0 for x in range(3)]
    rearAccels = [0 for x in range(3)]
    rearNewAccels = [0 for x in range(3)]
    accelUtilities = [0 for x in range(3)]
    
    #Where I can go
    myAccels[0] = self.calcAccel(nears[0]) if self.curLane > 0 else -100000
    myAccels[1] = self.calcAccel(nears[2])
    myAccels[2] = self.calcAccel(nears[4]) if self.curLane < TOTALLANES else -10000
    
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
    accelUtilities[0] = myAccels[0] - self.politeness * (rearAccels[0] + rearNewAccels[1])
    accelUtilities[2] = myAccels[2] - self.politeness * (rearAccels[2] + rearNewAccels[1])
    
    #print(self.name)
    #print(accelUtilities)
    
    #We've found our possible accelerations, and the effect of them on our neighbors.
    #But we can only merge if we aren't already mid merge
    whichLane = 1
    if(accelUtilities[2] + LTORBIAS >= THRESHOLD and not self.passing and self.isSafe(nears[0], nears[1])):
      #Merge right
      self.curAccel = myAccels[2]
      whichLane = 2
      self.targetLane = self.curLane + 1
      self.passing = True
    elif(accelUtilities[0] + RTOLBIAS >= THRESHOLD and not self.passing and self.isSafe(nears[4], nears[5])):
      #Merge left
      self.curAccel = myAccels[0]
      self.targetLane = self.curLane - 1
      whichLane = 0
      self.passing = True
    else:
      #Stay here
      self.curAccel = myAccels[1]
      whichLane = 1
      
    if(self.passing):
      if(self.curLane > self.targetLane):
        self.ypos -= 3
      else:
        self.ypos += 3
      
      if(GetLane(self.ypos) == self.targetLane):
        self.curLane = self.targetLane
        self.passing = False
    
    self.curVel += self.curAccel
    self.xpos += self.curVel
    #Check for crashes
    collisions = pygame.sprite.spritecollide(self, carGroup, False)
    if(len(collisions) > 1):
      self.color = RED
    #Draw
    self.rect = pygame.Rect(self.xpos, self.ypos, self.length, self.height)
    pygame.draw.rect(screen, self.color, self.rect)
    
  def calcAccel(self, ahead):
    vav0d = (self.curVel / self.desVel) ** 4
    #print("vav0d: " + str(vav0d))
    
    sStarTerm1 = self.minSpace
    sStarTerm2 = self.curVel * self.desTimeHeadway
    sStarTerm3Num = self.curVel - ahead.curVel
    sStarTerm3Denom = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
    sStarTerm3 = sStarTerm3Num / sStarTerm3Denom
    
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
    #Check ahead
    sStarTerm1A = self.minSpace
    sStarTerm2A = self.curVel * self.desTimeHeadway
    sStarTerm3NumA = self.curVel - ahead.curVel
    sStarTerm3DenomA = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
    sStarTerm3A = sStarTerm3NumA / sStarTerm3DenomA
    
    sAlphaA = ahead.xpos - self.xpos - ahead.length
    if(sAlphaA == 0):
      #Results in a crash. lim -> -oo, so we're returning a really negative number
      return False
    
    sStarA = sStarTerm1A + sStarTerm2A * math.exp(sStarTerm3A)
    
    #Check behind
    sStarTerm1B = self.minSpace
    sStarTerm2B = self.curVel * self.desTimeHeadway
    sStarTerm3NumB = self.curVel - behind.curVel
    sStarTerm3DenomB = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfBrake)
    sStarTerm3B = sStarTerm3NumB / sStarTerm3DenomB
    
    sAlphaA = self.xpos - behind.xpos - self.length
    if(sAlphaA == 0):
      #Results in a crash. lim -> -oo, so we're returning a really negative number
      return False
    
    sStarB = sStarTerm1B + sStarTerm2B * math.exp(sStarTerm3B)
    
    if(sStarA >= self.safetyCrit and sStarB >= self.safetyCrit):
      return True
    
    return False
    
#START UP SPRITES
#self, x, y, startVel, desVel, desMinGap, brake, p, minSpace, dTh, l, h, maxAcc, safeCrit, name
car1 = CarSprite(50, GetYForLane(1), 0, 30, 1, 1, 0, 1, 1, 10, 5, 1, 1, "car1")
car2 = CarSprite(150, GetYForLane(1), 0, 15, 1, 1, 0, 1, 1, 10, 5, 1, 1, "car2")
cars = [car1, car2]

#Add dummy cars beyond infinity, so we can avoid ugly cases in calcAccel
for i in range(-1, TOTALLANES + 2):
  endDummyCar = CarSprite(XLIMIT, GetYForLane(i), 120, 120, 1, 1, 1, 1, 1, 1, 1, 1, 1, "dummy")
  cars.append(endDummyCar)
  startDummyCar = CarSprite(-XLIMIT, GetYForLane(i), 120, 120, 1, 1, 1, 1, 1, 1, 1, 1, 1, "dummy")
  cars.append(startDummyCar)

carGroup = pygame.sprite.RenderPlain(*cars)
  
curTime = 0
    
#GAME LOOP
while 1:
  
  #USER INPUT
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  
  #UPDATE STUFF
  screen.fill(BLACK)
  DrawLanes(6)
  
  carGroup.update(carGroup)
  
  clock.tick(10)
  curTime += 1
  pygame.display.flip()