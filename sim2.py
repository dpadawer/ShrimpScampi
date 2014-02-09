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
    print("Updating " + self.__repr__())
    nears = self.calcNears(carGroup)
    myAccels = [0 for x in range(3)]
    rearAccels = [0 for x in range(3)]
    
    myAccels[0] = self.calcAccel(nears[0])
    myAccels[1] = self.calcAccel(nears[2])
    myAccels[2] = self.calcAccel(nears[4])
    
    rearAccels[0] = nears[1].calcAccel(self)
    rearAccels[1] = nears[3].calcAccel(self)
    rearAccels[2] = nears[5].calcAccel(self)
    
    self.curAccel = myAccels[1]
    
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
    print("vav0d: " + str(vav0d))
    
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
    print("sStar / sAlpha squared: " + str(finalTerm))
    
    calcedAccel = self.maxAccel * (1 - vav0d - finalTerm)
    print("Returning " + str(calcedAccel))
    return calcedAccel

  def calcNears(self, carGroup):
    print("calcNears for " + self.__repr__())
    dists = [sys.maxint for x in range(6)]
    nears = [None for x in range(6)]
    for car in carGroup:
      if(car == self): continue
      curDist = math.fabs(self.xpos - car.xpos)
      print("Looking at car " + car.__repr__())
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
    
    print("calcNears returning " + str(nears))
    return nears

#START UP SPRITES
#self, x, y, startVel, desVel, desMinGap, brake, p, minSpace, dTh, l, h, maxAcc, safeCrit, name
car1 = CarSprite(50, GetYForLane(1), 0, 30, 1, 1, 1, 1, 1, 10, 5, 1, 1, "name")
cars = [car1]

#Add dummy cars beyond infinity, so we can avoid ugly cases in calcAccel
for i in range(-1, TOTALLANES + 1):
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
  
  carGroup.update(carGroup)
  
  clock.tick(10)
  curTime += 1
  pygame.display.flip()