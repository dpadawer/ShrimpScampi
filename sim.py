#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

# INTIALISATION
import pygame, math, sys
import random
from pygame.locals import *
screen = pygame.display.set_mode((1920, 760), FULLSCREEN)
clock = pygame.time.Clock()

TOTAL_LANES = 1
THRESHOLD = .1
LTORBIAS = 0
RTOLBIAS = 0
XLIMIT = 1920 * 20
EPSILON = .01
DMG = 2
COMFORTBRAKE = 3
MINSPACE = 20
DTH = 1.5
LENGTH = 5
MAXACCEL = 1
SAFETYCRIT = 10
TIMEWARP = 1

SPAWNTHRESHOLD = .65

TOPBUF = 9

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
    
    self.safetyCrit = SAFETYCRIT
    
    self.length = length
    
    self.curLane = int((self.ypos - TOPBUF) / 9)
    self.targetLane = int((self.ypos - TOPBUF) / 9)
    
    self.maxAccel = maxAcceleration
    self.comfortBrake = comfortableBraking
    self.pol = politeness
    self.minSpacing = minSpace
    self.desTimeHeadway = desTimeHead
    
    self.rect = pygame.Rect(self.xpos, self.ypos, 5, 2)
    
    self.crashed = False
    self.passing = False
    
    self.color = ((0, 255, 0))
    
  def __repr__(self):
    return self.name + "={Pos: " + str((self.xpos, self.ypos)) + "; curVel, desVel: " + str((self.curVel, self.desVel)) + "; curLane, targetLane: " + str((self.curLane, self.targetLane)) + ", Color: " + str(self.color) + ", Passing?: " + str(self.passing) + "}"
    
    
  #Problem: if we update acc, vel, and pos all in one pass, there is simultaneousness being removed
  #Hacky solution: 2 passes - first is update acc/vel, second is position
  #We claim this is valid (with regards to possesing a lane) since people (hopefully) use their blinker
  def update(self, deltat, carGroup, passNo, screen):
    # SIMULATION
    #print("Updating " + self.__repr__() + ". Pass " + str(passNo))
      
    if(self.xpos <= -200 or self.ypos >= 760 or self.ypos <= -200):
      carGroup.remove(self)
      self.kill()
      return
      
    if(self.xpos >= XLIMIT):
      
      carGroup.remove(self)
      return
      '''
      self.xpos = self.xpos - XLIMIT
      self.ypos = self.ypos + 150
      '''
      
    if(passNo == 0):
      self.color = ((0, 255, 0))
    
      nears = self.findNears(carGroup)
      #print(nears)
      
      accels = self.calcAccels(nears, carGroup)
      #print("Calculated accels:")
      #print(accels)
      
      accels[0] = accels[0] + RTOLBIAS
      accels[2] = accels[2] + LTORBIAS
      
      #print(self.name)
      #print("Modified accels:")
      #if(self.curLane == 1 and not self.passing):
      #print(accels)

      which = accels.index(max(accels))
      #if(self.curLane == 1 and not self.passing):
      #print("Desired is " + str(which))
      
      if(accels[2] >= accels[1] + THRESHOLD and accels[2] >= accels[0] + THRESHOLD):
        which = 2
      elif(accels[1] >= accels[2] + THRESHOLD and accels[1] >= accels[0] + THRESHOLD):
        which = 1
      else:
        which = accels.index(max(accels))

      accels[0] = accels[0] - RTOLBIAS
      accels[2] = accels[2] - LTORBIAS

      #print("Chose " + str(which))
      
      #print("Passing? " + str(self.passing))
      
      if(max(accels) < -20):
        car_group.remove(self)
        return
      
      if(not self.passing):
        if(which == 2 and self.isSafe(nears[4], nears[5], SAFETYCRIT)):
          #Merge right
          self.targetLane = self.curLane + 1
          self.curAcc = accels[2]
          self.passing = True
          #print("Switching right")
        elif(which == 0 and self.isSafe(nears[0], nears[1], SAFETYCRIT)):
          #Merge left
          self.targetLane = self.curLane - 1
          self.curAcc = accels[0]
          self.passing = True
          #print("Switching left")
        else:
          #Don't bother
          self.targetLane = self.curLane
          self.curAcc = accels[1]
          #if(self.curLane == 1 and not self.passing):
            #print("Staying put")
      else:
        self.curAcc = accels[1]
        
      self.curVel = self.curVel + self.curAcc
        
    elif(passNo == 1):      
      self.xpos = self.xpos + self.curVel
      
      if(self.curLane > self.targetLane):
        #print(self.ypos)
        self.ypos = self.ypos - 3
        #print("Moving left")
        #print(self.ypos)
        #self.curLane = self.targetLane
      elif(self.curLane < self.targetLane):
        #print(self.ypos)
        self.ypos = self.ypos + 3
        #print("Moving right")
        #print(self.ypos)
        #self.curLane = self.targetLane
      
      if(self.ypos % 9 == 0):
        self.curLane = self.targetLane
        #print("Set curLane of " + self.__repr__() + " to " + str(self.curLane) + ", target lane is " + str(self.targetLane))
        self.targetLane = self.curLane
        self.passing = False
      #else:
        #self.color = ((0, 0, 255))
        #print(self.__repr__())
      
      #print(self.name)
      self.rect = self.src_image.get_rect()
      #print(self.xpos, int(self.xpos))
      self.rect.centerx = int(self.xpos)
      #print(self.ypos, int(self.ypos))
      self.rect.centery = int(self.ypos)
      
      self.happiness = math.fabs(self.curVel - self.desVel)
      
    #So wrong.
    if(passNo == 2):
      carsHit = pygame.sprite.spritecollide(self, carGroup, False)
      # > 1 instead of > 0 since spritecollide(car, carGroup) will always return it crashed with itself
      if(len(carsHit) > 1):
        self.crashed = True
      else:
        self.crashed = False
      
      if(self.happiness <= 5):
        self.color = ((0, 255, 0))
      elif(self.happiness <= 10):
        self.color = ((0, 0, 255))
      else:
        self.color = ((255, 0, 0))
      
      if(self.crashed):
        self.color = ((255, 255, 255))
        self.curVel = self.curVel / 2
        tmp = self.curLane
        self.curLane = self.targetLane
        self.targetLane = tmp
        
      pygame.draw.rect(screen, self.color, self.rect)  
    
    #print("Finished updating " + self.__repr__())
    if(self.curVel < 0):
      #print(self.name + " has a velocity of " + str(self.curVel))
      self.curVel = 0
      #sys.exit(0)      
    
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
        accels[0] = self.maxAccel * self.calcAccelFree()
      else:
        accels[0] = self.maxAccel * self.calcAccelInt(nears[0], carGroup)
      
    if(nears[2] == None):
      accels[1] = self.maxAccel * self.calcAccelFree()
    else:
      accels[1] = self.maxAccel * self.calcAccelInt(nears[2], carGroup);
    
    if(self.curLane == TOTAL_LANES - 1):
      accels[2] = -sys.maxint
    else:
      if(nears[4] == None):
        accels[2] = self.maxAccel * self.calcAccelFree()
      else:
        accels[2] = self.maxAccel * self.calcAccelInt(nears[4], carGroup);
        
    if(not self.isSafe(nears[0], nears[1], self.safetyCrit)):
      #print("left not safe")
      accels[0] = -sys.maxint
      
    if(not self.isSafe(nears[4], nears[5], self.safetyCrit)):
      #print("right not safe")
      accels[2] = -sys.maxint
      
    return accels
  
  def calcAccelDanny(self, ahead):      
    if(self.curVel <= self.desVel):
      if(ahead == None):
        #Treat as at infinity
        return min((self.desVel - self.curVel / self.desVel), self.maxAccel)
      else:
        return min((self.desVel - min(self.curVel, ahead.curVel)) / self.desVel, self.maxAccel)
    else:
      return -min(math.fabs(self.comfortBrake), math.fabs((self.desVel - self.curVel) / self.desVel))
  
  def calcAccelFree(self):
    #print("calcAccelFree Returning " + str(self.maxAccel * (1 - ((self.curVel / self.desVel) ** 4))))
    return (1 - ((self.curVel / self.desVel) ** 4))
  
  def calcAccelInt(self, ahead, carGroup):      
    #print("self: " + self.__repr__())
    #print("ahead: " + ahead.__repr__())
      
    #delvalpha = self.curVel - ahead.curVel
    delvalpha = self.curVel - ahead.curVel
    if(math.fabs(delvalpha) > 250):
      print("dangerous delvalpha found: self: " + self.__repr__() + "; ahead: " + ahead.__repr__())
    #print("self.curVel: " + str(self.curVel) + ", ahead.curVel: " + str(ahead.curVel))
    
    '''
    term3Num = self.curVel * delvalpha
    term3Denom = 2 * math.sqrt(self.maxAccel * self.comfortBrake)
    
    term3 = term3Num / term3Denom
    term2 = self.curVel * self.desTimeHeadway
    term1 = self.minSpacing
    
    sstar = term1 + term2 + term3
    '''
    
    term1 = self.minSpacing
    term2 = self.desTimeHeadway * self.curVel
    term3Num = delvalpha
    term3Denom = 2 * self.desTimeHeadway * math.sqrt(self.maxAccel * self.comfortBrake)
    term3 = term3Num / term3Denom
    
    actualTerm2 = math.exp(term3) * term2
    
    sstar = term1 + actualTerm2
    
    salpha = ahead.xpos - self.xpos - ahead.length
      
    if(salpha == 0):
      #print("calcAccelInt Returning -sys.maxint")
      return -sys.maxint
    
    freeAccel = self.calcAccelFree()
    
    interim = (sstar ** 2) / (salpha ** 2)
    
    #print("calcAccelInt Returning " + str(-self.maxAccel * ((sstar / salpha) ** 2)))
    return (freeAccel - interim)
    
  #TODO: Potentially set different safety criteria for ahead and behind
  def isSafe(self, aheadCar, behindCar, safetyCrit):
    #Account for length?
    #print("In isSafe with " + self.name)
    forwardVal = 0
    behindVal = 0
    if(aheadCar == None):
      forwardVal = sys.maxint
    else:
      forwardVal = math.fabs(aheadCar.xpos - self.xpos)
      forwardVal = self.desMinGap + self.curVel * self.desTimeHeadway
      
    #print(forwardVal)
    
    if(behindCar == None):
      behindVal = sys.maxint
    else:
      behindVal = math.fabs(behindCar.xpos - self.xpos)
      behindVal = self.desMinGap + behindCar.curVel * self.desTimeHeadway

    #print(behindVal)
    
    if(forwardVal > safetyCrit and behindVal > safetyCrit):
      #print("Returning true")
      return True
    
    #print("Returning false")
    return False
    


def DrawRoad(screen, startY):
  pygame.draw.line(screen, (255, 255, 255), [0, startY], [1920, startY], 1)
  for i in range(1, TOTAL_LANES):
    pygame.draw.line(screen, (125, 125, 125), [0, startY + 9 * i], [1920, startY + 9 * i], 1)
  pygame.draw.line(screen, (255, 255, 255), [0, startY + TOTAL_LANES * 9], [1920, startY + TOTAL_LANES * 9], 1)

def GetLaneStats(laneNo, carGroup):
  totalR = 0
  totalB = 0
  totalG = 0
  totalCurSpeed = 0
  totalDesSpeed = 0
  for car in carGroup:
    if(car.curLane != laneNo): continue
    if(car.happiness <= 5):
      totalG = totalG + 1
    elif(car.happiness <= 10):
      totalB = totalB + 1
    else:
      totalR = totalR + 1
    
    totalCurSpeed = totalCurSpeed + car.curVel
    totalDesSpeed = totalDesSpeed + car.desVel
    
  totalCars = totalR + totalB + totalG
  
  avgCurSpeed = 0 if totalCars == 0 else totalCurSpeed / totalCars
  avgDesSpeed = 0 if totalCars == 0 else totalDesSpeed / totalCars
  
  print("(R, G, B): " + str((totalR, totalG, totalB)) + "; Average Speeds (cur, des): " + str((avgCurSpeed, avgDesSpeed)))
  
  
def DumpAll(carGroup, curTime):
  for car in carGroup:
    print(str((curTime, car.name, car.curLane, car.targetLane, car.curVel, car.desVel, car.xpos, car.ypos, car.curAcc)))
  
  
# Make a couple of cars
#img, xPos, yPos, startVel, desVel, DMG, comfortBrake, politeness, minSpace, DTH, len, maxAcc):
'''
car1 = CarSprite('car1.png', 50, TOTAL_LANES * 9, 30, 45, 10, 3, 1, 5, 1.5, 10, 1, "Car1") #Red
car2 = CarSprite('car2.png', 75, TOTAL_LANES * 9, 24, 35, 10, 3, 1, 5, 1.5, 10, 1, "Car2") #Blue
car3 = CarSprite('car3.png', 100, TOTAL_LANES * 9, 21, 25, 10, 3, 1, 5, 1.5, 10, 1, "Car3") #Green
cars = [car1, car2, car3]
#cars = [car1]
'''

'''
car1 = CarSprite('car' + str(random.randint(1,3)) + ".png", 50, 9 * TOTAL_LANES, 30, 45, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car1")
car2 = CarSprite('car' + str(random.randint(1,3)) + ".png", 75, 9 * TOTAL_LANES, 30, 35, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car2")
car3 = CarSprite('car' + str(random.randint(1,3)) + ".png", 100, 9 * TOTAL_LANES, 30, 24, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car3")
car4 = CarSprite('car' + str(random.randint(1,3)) + ".png", 50, 9 * (TOTAL_LANES - 1), 30, 45, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car4")
car5 = CarSprite('car' + str(random.randint(1,3)) + ".png", 75, 9 * (TOTAL_LANES - 1), 30, 35, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car5")
car6 = CarSprite('car' + str(random.randint(1,3)) + ".png", 100, 9 * (TOTAL_LANES - 1), 30, 25, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car6")

cars = [car1, car2, car3, car4, car5, car6]
'''

'''
car1 = CarSprite('car1.png', 50, 14, 25, 60, 2, 3, 1, 5, 1.5, 1, 1, "Car1") #Red
car2 = CarSprite('car2.png', 100, 14, 25, 30, 2, 3, 1, 5, 1.5, 1, 1, "Car2") #Blue
car3 = CarSprite('car3.png', 150, 14, 25, 30, 2, 3, 1, 5, 1.5, 1, 1, "Car3") #Green



'''
'''

for i in range(10):
  car = CarSprite('car' + str(random.randint(1,3)) + ".png", 50 * i + 50, TOPBUF + (TOTAL_LANES - 1) * 9, 25, 54 - 3 * i, DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(i))
  print("Created " + car.name + " with speed " + str(car.curVel) + " and des speed " + str(car.desVel) + " at pos " + str((car.xpos, car.ypos)))
  cars.append(car)
'''

cars = []
car_group = pygame.sprite.RenderPlain(*cars);

curTime = 0

while 1:
  # USER INPUT
  deltat = clock.tick(10)  
  
  '''
  if(addIdx % 2 == 0 and len(cars) < 1000):
    for i in range(TOTAL_LANES - 2, TOTAL_LANES):
      startVel = random.randint(30, 50) / TIMEWARP
      #car = CarSprite('car' + str(random.randint(1,3)) + ".png", random.randrange(25, 75, 25), random.randrange(9, 9 * TOTAL_LANES, 9), startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
      #car = CarSprite('car' + str(random.randint(1,3)) + ".png", random.randrange(25, 75, 25), 9 * TOTAL_LANES, startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
      car = CarSprite('car' + str(random.randint(1,3)) + ".png", 0, 9 * (i + 1), startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
     
      nears = car.findNears(car_group)
      if(car.isSafe(nears[2], None, SAFETYCRIT) and max(car.calcAccels(nears, car_group)) >= 0):
        cars.append(car)
        car_group = pygame.sprite.RenderPlain(*cars)
        #print("Added car:")
        #print(car.__repr__())
  '''
  
  if(addIdx % 3 == 0 and len(cars) < 1000):
    for i in range(0, TOTAL_LANES):
      for j in range(0, 1):
        startVel = random.randint(30, 33) / TIMEWARP
        #car = CarSprite('car' + str(random.randint(1,3)) + ".png", random.randrange(25, 75, 25), random.randrange(9, 9 * TOTAL_LANES, 9), startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
        #car = CarSprite('car' + str(random.randint(1,3)) + ".png", random.randrange(25, 75, 25), 9 * TOTAL_LANES, startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
        car = CarSprite('car' + str(random.randint(1,3)) + ".png", j * 50, 9 * (i + 1), startVel, startVel + (random.randint(-10, 10) / TIMEWARP), DMG, COMFORTBRAKE, 1, MINSPACE, DTH, LENGTH, MAXACCEL, "Car" + str(len(cars)))
       
        nears = car.findNears(car_group)
        if(car.isSafe(nears[0], None, SAFETYCRIT) and car.isSafe(nears[2], None, SAFETYCRIT) and car.isSafe(nears[4], None, SAFETYCRIT) and max(car.calcAccels(nears, car_group)) >= 0):
          if(random.random() >= SPAWNTHRESHOLD):
            cars.append(car)
            car_group = pygame.sprite.RenderPlain(*cars)
          #print("Added car:")
          #print(car.__repr__())
  
  
  #print("TICK")
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  # RENDERING
  
  screen.fill((0,0,0))
  
  DrawRoad(screen, 5)
  DrawRoad(screen, 155)
  DrawRoad(screen, 305)
  DrawRoad(screen, 455)
  DrawRoad(screen, 605)

  car_group.update(deltat, car_group, 0, screen)
  #print("TOCK")
  car_group.update(deltat, car_group, 1, screen)
  
  
  #for car in car_group:
    #print(car.__repr__())
  
  
  car_group.update(deltat, car_group, 2, screen)
  pygame.display.flip()
  #print("")
  '''
  for i in range(TOTAL_LANES):
    print("Lane " + str(i) + ":")
    GetLaneStats(i, car_group)
  '''
  #DumpAll(car_group, curTime)
  curTime = curTime + 1
  #if(curTime >= 500):
  #  sys.exit(0)
  
  addIdx = addIdx + 1
