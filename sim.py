#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

# INTIALISATION
import pygame, math, sys
from pygame.locals import *
screen = pygame.display.set_mode((1024, 768))
clock = pygame.time.Clock()

TOTAL_LANES = 2
THRESHOLD = 0.1

#Since a car is 5 pixels wide, we will define a lane as 9 pixels
#Lane centers will start at y = 5 (then 24, 33, 42...)

class CarSprite(pygame.sprite.Sprite):
  def __init__(self, image, xposition, yposition, startVelocity, desiredVelocity, desiredMinGap, comfortableBraking, politeness, minSpace, desTimeHead, length, maxAcceleration, name):
    pygame.sprite.Sprite.__init__(self)
    self.src_image = pygame.image.load(image)
    self.xpos = xposition
    self.ypos = yposition
    
    self.name = name
    
    self.curVel = startVelocity
    
    self.curAcc = 0
    
    self.desVel = desiredVelocity
    self.desMinGap = desiredMinGap
    
    self.length = length
    
    self.curLane = int(round((self.ypos - 5) / 9))
    self.targetLane = int(round((self.ypos - 5) / 9))
    
    self.maxAccel = maxAcceleration
    self.comfortBrake = comfortableBraking
    self.pol = politeness
    self.minSpacing = minSpace
    self.desTimeHeadway = desTimeHead
    
  #Problem: if we update acc, vel, and pos all in one pass, there is simultaneousness being removed
  #Hacky solution: 2 passes - first is update acc/vel, second is position
  #We claim this is valid (with regards to possesing a lane) since people (hopefully) use their blinker
  def update(self, deltat, carGroup, passNo):
    # SIMULATION
    print("Updating " + self.name + ". Pass " + str(passNo))
    if(self.name == "Car1"):
      print(self.curLane)
      print(self.targetLane)
      #print(self.xpos, self.ypos)
      print(self.curVel, self.desVel)
    
    self.curLane = int(round((self.ypos - 5) / 9))
      
    if(self.xpos >= 1200 or self.xpos <= -200 or self.ypos >= 1000 or self.ypos <= -200):
      carGroup.remove(self)
      return
    
    if(passNo == 0):
      nears = self.findNears(carGroup)

      accels = self.calcAccels(nears)
      print(accels)

      which = accels.index(max(accels))
      print("Largest " + str(which))
      
      if(which == 0 and accels[0] - accels[1] > THRESHOLD):
        #Merge left
        self.targetLane = self.curLane - 1
        self.curAcc = accels[0]
      elif(which == 2 and accels[2] - accels[1] > THRESHOLD):
        self.targetLane = self.curLane + 1
        self.curAcc = accels[2]
      else:
        self.targetLane = self.curLane
        self.curAcc = accels[1]
        
      self.curVel = self.curVel + self.curAcc
        
    else:      
      self.xpos = self.xpos + self.curVel
      self.ypos = self.curLane * 9 + 5
      
      if(self.curLane > self.targetLane):
        self.ypos = self.ypos - 9
      elif(self.curLane < self.targetLane):
        self.ypos = self.ypos + 9

      self.rect = self.src_image.get_rect()
      self.rect.centerx = self.xpos
      self.rect.centery = self.ypos
      self.image = self.src_image
    
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
      dist = car.xpos - self.xpos
      if(car.curLane == self.curLane + 1 or car.targetLane == self.curLane + 1):
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
      elif(car.curLane == self.curLane - 1 or car.targetLane == self.curLane - 1):
        if(car.xpos >= self.xpos):
          if(dist < dists[4]):
            nears[4] = car
            dists[4] = dist
        else:
          if(dist < dists[5]):
            nears[5] = car
            dists[5] = dist
    
    return nears
    
  def calcAccels(self, nears):
    accels = [0 for x in range(3)]
    
    if(self.curLane == 0):
      accels[0] = -sys.maxint
    else:
      if(nears[0] == None):
        accels[0] = self.calcAccelFree()
      else:
        accels[0] = self.calcAccelInt(nears[0])
      
    if(nears[2] == None):
      accels[1] = self.calcAccelFree()
    else:
      accels[1] = self.calcAccelInt(nears[2]);
    
    if(self.curLane == TOTAL_LANES - 1):
      accels[2] = -sys.maxint
    else:
      if(nears[4] == None):
        accels[2] = self.calcAccelFree()
      else:
        accels[2] = self.calcAccelInt(nears[4]);
      
    return accels
    
  def calcAccelFree(self):
    #print("In calcAccelFree")
    #print("Returning " + str(self.maxAccel * (1 - ((self.curVel / self.desVel) ** 4))))
    return self.maxAccel * (1 - ((self.curVel / self.desVel) ** 4))
  
  def calcAccelInt(self, near):
    #print("In calcAccelInt")
    delvalpha = self.curVel - near.curVel
    sstar = self.minSpacing + (self.curVel * self.desTimeHeadway) + ((self.curVel * delvalpha) / (2 * math.sqrt(self.maxAccel * self.comfortBrake)));
    salpha = near.xpos - self.xpos - near.length
    
    freeAccel = self.calcAccelFree()
    
    #print("Returning " + str(-self.maxAccel * ((sstar / salpha) ** 2)))
    return self.maxAccel * (freeAccel - ((sstar / salpha) ** 2))
    
# Make a couple of cars
#img, xPos, yPos, startVel, desVel, DMG, comfortBrake, politeness, minSpace, DTH, l, maxAcc):
car1 = CarSprite('car1.png', 50, 14, 30, 35, 2, 3, 1, 2, 1.5, 1, 1, "Car1") #Red
car2 = CarSprite('car2.png', 200, 14, 24, 25, 2, 3, 1, 2, 1.5, 1, 1, "Car2") #Blue
car3 = CarSprite('car3.png', 350, 14, 21, 25, 2, 3, 1, 2, 1.5, 1, 1, "Car3") #Green

cars = [car1, car2, car3]
#cars = [car1]

car_group = pygame.sprite.RenderPlain(*cars);


while 1:
  # USER INPUT
  deltat = clock.tick(1)
  
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

