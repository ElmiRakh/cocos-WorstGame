from cocos.layer import Layer

import pyglet
from pyglet.gl import *

pyglet.resource.path = ['/home/elmirakh/pygletapp/resources/']
pyglet.resource.reindex()

class BackgroundLayer( Layer ):
    def __init__(self):
        super( BackgroundLayer, self ).__init__()
        self.img = pyglet.resource.image('background/background.png')

    def draw( self ):
        glPushMatrix()
        self.transform()
        self.img.blit(0,0)
        glPopMatrix()