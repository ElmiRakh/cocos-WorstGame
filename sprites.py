import sys
from os import path

import pyglet
import cocos
import math

from cocos.sprite import Sprite
from cocos.actions import RotateBy,MoveTo,FadeOut,Delay,Repeat,Bezier,Place,Reverse,MoveBy,Accelerate
import cocos.collision_model as cm
import cocos.euclid as eu

res_path = path.join(path.abspath(path.curdir),'resources')

res = pyglet.resource.Loader(res_path)
res.reindex()

class Planet( Sprite ):
    def __init__(self,position,imgname,batch=None,radius=1):
        image = res.image('planets/' + imgname)
        super(Planet, self).__init__(image)
        self.name = imgname.split('.')[0]
        self.position = position
        self.scale = 1.0

        if batch:
            batch.add(self,name=self.name)
        
class Ship( Sprite ):
    def __init__(self,position,batch=None,name=None):
        image = res.image('fleet/spaceship.png')
        super(Ship, self).__init__(image)
        self.position = position
        self.rotation = 45
        self.scale = 0.5
        self.name = name
        self.orig_pos = position
        self.last_action = ()
        if batch:
            batch.add(self)
        
    def spawn(self,x_,y_,time):
        x,y = self.orig_pos
        angle = math.degrees(math.atan2(y_-y,x_-x))
        self.last_action = (x_,y_,time)
        actions =  Repeat(RotateBy(angle,0.25) + MoveTo((x_,y_),time) + RotateBy(angle,0.25) + Accelerate((MoveTo((x,y),time)), 4))
        self.do(actions)

    def repeat(self):
        x_,y_,time = self.last_action
        self.spawn(x_,y_,time)

    def end(self):
        self.kill()