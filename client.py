import sys
from PodSixNet.Connection import ConnectionListener, connection
from time import sleep,localtime
from simplejson import loads
import cocos
import math
from cocos.text import Label
from cocos.director import director
from cocos.menu import *
from cocos.scene import *
from cocos.layer import *
from cocos.actions import InstantAction,CallFunc
from cocos.sprite import Sprite
import pyglet
from cocos.actions import MoveBy,MoveTo,Rotate,Delay,Repeat
from pyglet.window import mouse
import numpy as np
from cocos.batch import BatchNode
from sprites import Planet, Ship
from constants import *
from background import BackgroundLayer
from cocos.menu import Menu,MenuItem,ToggleMenuItem,fixedPositionMenuLayout,shake
from time import sleep

class MainMenu( Menu ):
	def __init__(self):
		
		super( MainMenu, self).__init__('Awful Space Conquerors') 
		
		self.font_title['font_name'] = 'Helvetica'
		self.font_title['font_size'] = 64
		self.font_title['color'] = (128,128,0,255)

		self.font_item['font_name'] = 'Edit Undo Line BRK',
		self.font_item['color'] = (32,64,128,255)
		self.font_item['font_size'] = 48
		self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
		self.font_item_selected['color'] = (32,16,64,255)
		self.font_item_selected['font_size'] = 48
		
		self.menu_anchor_y = 'center'
		self.menu_anchor_x = 'center'
		items = []

		items.append( MenuItem('Play game', self.on_host) )
		items.append( ToggleMenuItem('Show FPS:', self.on_show_fps, director.show_FPS) )
		items.append( MenuItem('Quit', self.on_quit) )

		self.create_menu( items,shake(), shake(),layout_strategy=fixedPositionMenuLayout([(600,550),(600,400),(600,300),(600,200)]) )
		
	def on_host(self):
		director.replace(Scene(PlanetsGame()))

	def on_show_fps(self, value):
		director.show_FPS = value

	def on_quit(self):
		exit()

class PlanetsGame(ConnectionListener,Layer):
	is_event_handler=True

	def Network_close(self, data):
		exit()

	def Network_connected(self, data):
		print('Connected')

	def Network_init(self,data):
		print(data['players'])
		self.state = loads(data["state"])
		self.players = data['players']
		

	def Network_players(self, data):
		self.players = data['players']
		print(self.players)

	def Network_nickname(self,data):
		self.player = data['nickname']

	def Network_error(self, data):
		pass

	def Network_state(self, data):
		self.state = loads(data["state"])

	def __init__(self,initials=initials,host='127.0.0.1',port='7636'):
		self.players = 0
		self.state = {}
		self.player = None

		self.Connect((host,int(port)))
		connection.Pump()
		self.Pump()
		
		
		print(self.player)
		connection.Send({'action':'ready'})
		while self.players < 2:
			sleep(0.1)
			connection.Pump()
			self.Pump()
		
		self.initials = initials

		Layer.__init__(self)
		self.background = BackgroundLayer()

		self.planets = BatchNode()
		self.fleets = BatchNode()
		self.label = dict()
		
		self.planet_list = []
		self.fleet_list = []
		
		self.init_ui()

		self.selected = []

		self.add(self.planets,z=1,name='Planets')
		self.add(self.fleets, z=2,name='Fleets')
		self.schedule_interval(self.update,1.25)
		self.draw()


	def update_text(self):
		for name,lbl in self.label.items():
			lbl.element.text = str(self.state[name]['fleet'])

	def init_ui(self):
		self.add(self.background,z=-1)
		for imgname,position in self.initials.items():
			self.planet_list.append(Planet(imgname=imgname,position=position,batch=self.planets))
			name = imgname.rstrip('.png')
			self.label[name] = Label(text=str(0),position=position,font_name='Helvetica')
			self.add(self.label[name] ,name=name,z=3)

	def reset_all(self):
		for planet in self.planets.get_children():
			self.reset(planet)
			
	def check_selection(self,x,y):
		for planet in self.planets.get_children():
			if planet.contains(x,y):
				return planet.name
			
	def on_mouse_press(self,x,y,buttons,modifier):
		_x, _y = director.get_virtual_coordinates(x, y)
		selection = self.check_selection(_x,_y)
		if not selection:
			self.reset_all()
			self.selected = []
			return
		if buttons == mouse.LEFT:
			if self.state[selection]['owner'] != self.player:
				self.reset_all()
				self.selected = []
			if self.state[selection]['owner'] == self.player:
				self.highlight_friend(self.planets.get(selection))
				self.selected.append(selection)
				return
			else:
				if self.state[selection]['owner'] not in ['neutral',self.player]:
					self.reset_all()
					self.selected = []
					self.highlight_enemy(self.planets.get(selection))
					return
				else:
					self.reset_all()
					self.selected = []
					self.highlight_neutral(self.planets.get(selection))
					return
		elif buttons == mouse.RIGHT:
			if self.selected and selection:
				for planetname in self.selected:
					connection.Send({'action':'sendfleet','start':planetname,'target':selection})
			self.reset_all()
			self.selected = []


	def update(self,dt):
		connection.Send({'action':'state'})
		connection.Pump()
		self.Pump()
		self.update_text()
		if self.state['winner']:
			if self.player == self.state['winner']['winner']:
				director.replace(Scene(Winner()))
			else:
				director.replace(Scene(Loser()))
		for planet in self.planets.get_children():
			if self.state[planet.name]['ett'] != 0:
				print(self.state[planet.name])
			if self.state[planet.name]['ett'] != 0:
				fleet = Ship(planet.position,batch=self.fleets,name=planet.name)
				target = self.state[planet.name]['target']
				x,y = self.planets.get(target).position
				self.transfer(fleet,x,y,self.state[planet.name]['ett'])
		for fleet in self.fleets.get_children():
			if self.state[fleet.name]['ett'] == 0:
				fleet.end()
			if not self.state[fleet.name]['active'] and self.state[fleet.name]['ett']+self.state[fleet.name]['start_step'] > self.state['step']:
				fleet.end()
					
		self.draw()

	@staticmethod        
	def highlight_friend(planet):
		planet.scale = 1.2
		planet.color = (25,255,25)
		
	@staticmethod        
	def highlight_enemy(planet):
		planet.scale = 1.2
		planet.color = (255,25,25)
		
	@staticmethod        
	def highlight_neutral(planet):
		planet.scale = 1.2
		planet.color = (100,100,100)
		
	@staticmethod    
	def reset(planet):
		planet.scale = 1.0
		planet.color = (255,255,255)
		
	@staticmethod
	def transfer(ship,x,y,time):
		ship.spawn(x,y,time)

class Winner(Layer):
	def __init__(self):
		super(Winner,self).__init__()
		self.background = BackgroundLayer()
		x,y = director.get_window_size()
		position = x//4,y//2
		self.label = Label(text='YOU WON',position=position,font_name='Helvetica',
						  font_size = 48)
		self.label2 = Label(text='But all your planets burned out',position=(x//10,y//4),font_name='Helvetica',
						font_size = 48)
		self.add(self.background,z=-1)
		self.add(self.label,z=1)
		self.add(self.label2,z=1)
		self.draw()

class Loser(Layer):
	def __init__(self):
		super(Loser,self).__init__()
		self.background = BackgroundLayer()
		x,y = director.get_window_size()
		position = x//4,y//2
		self.label = Label(text='YOU LOST',position=position,font_name='Helvetica',
						  font_size = 48)
		self.label2 = Label(text='But your enemy got only ashe in return',position=(x//10,y//4),font_name='Helvetica',
						font_size = 48)
		self.add(self.background,z=-1)
		self.add(self.label,z=1)
		self.add(self.label2,z=1)
		self.draw()   

if __name__ == '__main__':
	director.init(1200,900,caption='Planets')
	director.window.push_handlers(mouse)
	director.set_projection3D()
	director.set_depth_test()
	menu = Scene(MainMenu())
	director.run(menu)
	
