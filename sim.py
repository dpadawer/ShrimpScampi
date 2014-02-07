#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

# INTIALISATION
import pygame, math, sys
from pygame.locals import *
screen = pygame.display.set_mode((1024, 768))
clock = pygame.time.Clock()



class CarSprite(pygame.sprite.Sprite):
  def __init__(self, image, xposition, yposition, startVelocity, desiredVelocity, desiredMinGap, comfortableBraking, politeness, minSpace, desTimeHead, length, maxAcceleration, name):
    pygame.sprite.Sprite.__init__(self)
    self.src_image = pygame.image.load(image)
    self.xpos = xposition
    self.ypos = yposition
    
    self.name = name
    
    self.xcurVel = startVelocity
    self.ycurVel = 0
    
    self.xcurAcc = 0
    self.ycurAcc = 0
    
    self.desVel = desiredVelocity
    self.desMinGap = desiredMinGap
    
    self.length = length
    
    self.maxAccel = maxAcceleration
    self.comfortBrake = comfortableBraking
    self.pol = politeness
    self.minSpacing = minSpace
    self.desTimeHeadway = desTimeHead
    
  def update(self, deltat, carGroup):
    # SIMULATION
    print("Updating " + self.name)
    
    if(self.xpos >= 1200 or self.xpos <= -200 or self.ypos >= 1000 or self.ypos <= -200):
      carGroup.remove(self)
      return
    
    #Use carGroup to get the guy right in front of us
    shortestDist = sys.maxint
    nearestCar = None
    for car in carGroup:
      if (car == self): continue
      if (car.ypos != self.ypos): continue #different lane. TODO: Make it anyone entering the lane
      if (car.xpos < self.xpos): continue #behind us. Not what we're looking for (at least not here)
      dist = car.xpos - self.xpos
      if (dist < shortestDist):
        nearestCar = car
        shortestDist = dist
    
    if(nearestCar == None):
      print("No vehicle in front of " + self.name)
      tmp = self.maxAccel * (1 - ((self.xcurVel / self.desVel) ** 4))
      print("Old vel: " + str(self.xcurVel))
      self.xcurVel = self.xcurVel + tmp
      print("New vel: " + str(self.xcurVel))
    else:
      print("vehicle in front of " + self.name + " is " + nearestCar.name)
      
      delvalpha = self.xcurVel - nearestCar.xcurVel
      sstar = self.minSpacing + (self.xcurVel * self.desTimeHeadway) + ((self.xcurVel * delvalpha) / (2 * math.sqrt(self.maxAccel * self.comfortBrake)));
      salpha = self.xpos - nearestCar.xpos - nearestCar.length
      
      tmp = -self.maxAccel * ((sstar / salpha) ** 2)
      
      print("Old vel: " + str(self.xcurVel))
      self.xcurVel = self.xcurVel + tmp
      print("New vel: " + str(self.xcurVel))
      
    self.ycurAcc = 0
    
    #self.ycurVel = self.ycurVel
    
    self.xpos = self.xpos + self.xcurVel
    self.ypos = self.ypos + self.ycurVel
    
    self.rect = self.src_image.get_rect()
    self.rect.centerx = self.xpos
    self.rect.centery = self.ypos
    self.image = self.src_image
    
# Make a couple of cars
#img, xPos, yPos, startVel, desVel, DMG, comfortBrake, politeness, minSpace, DTH, l, maxAcc):
car1 = CarSprite('car1.png', 50, 50, 20, 30, 2, 3, 1, 2, 1.5, 10, 2, "Car1") #Red
car2 = CarSprite('car2.png', 300, 50, 20, 25, 2, 3, 1, 2, 1.5, 10, 2, "Car2") #Blue
car3 = CarSprite('car3.png', 550, 50, 20, 20, 2, 3, 1, 2, 1.5, 10, 2, "Car3") #Green
#car2 = CarSprite('car2.png', 50, 125, 3, 3, 1, 1, 1)
#car3 = CarSprite('car3.png', 50, 200, 4, 3, 1, 1, 1)

cars = [car1, car2, car3]

car_group = pygame.sprite.RenderPlain(*cars);


while 1:
  # USER INPUT
  deltat = clock.tick(30)
  print("TICK")
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  # RENDERING
  screen.fill((0,0,0))
  car_group.update(deltat, car_group)
  car_group.draw(screen)
  pygame.display.flip()

