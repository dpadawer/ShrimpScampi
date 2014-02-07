#Based on Rapid Game Development In Python, by Richard Jones
#http://osdcpapers.cgpublisher.com/product/pub.84/prod.11/m.1?

# INTIALISATION
import pygame, math, sys
from pygame.locals import *
screen = pygame.display.set_mode((1024, 768))
clock = pygame.time.Clock()

class CarSprite(pygame.sprite.Sprite):
  def __init__(self, image, xposition, yposition, startVelocity, desiredVelocity, desiredMinGap, comfortableBraking, politeness):
    pygame.sprite.Sprite.__init__(self)
    self.src_image = pygame.image.load(image)
    self.xpos = xposition
    self.ypos = yposition
    self.xcurVel = startVelocity
    self.ycurVel = 0
    self.xcurAcc = 0
    self.ycurAcc = 0
    self.desVel = desiredVelocity
    self.desMinGap = desiredMinGap
    self.comfortBrake = comfortableBraking
    self.pol = politeness
  def update(self, deltat):
    # SIMULATION
    self.xcurVel = self.xcurVel + self.xcurAcc
    self.ycurVel = self.ycurVel + self.ycurAcc
    self.xpos = self.xpos + self.xcurVel
    self.ypos = self.ypos + self.ycurVel
    self.rect = self.src_image.get_rect()
    self.rect.centerx = self.xpos
    self.rect.centery = self.ypos
    self.image = self.src_image
    
# Make a couple of cars
rect = screen.get_rect()
car = CarSprite('car1.png', rect.centerx, rect.centery, 2, 3, 1, 1, 1)
car_group = pygame.sprite.RenderPlain(car)

while 1:
  # USER INPUT
  deltat = clock.tick(30)
  for event in pygame.event.get():
    if not hasattr(event, 'key'): continue
    down = event.type == KEYDOWN
    if event.key == K_ESCAPE: sys.exit(0)
  # RENDERING
  screen.fill((0,0,0))
  car_group.update(deltat)
  car_group.draw(screen)
  pygame.display.flip()

