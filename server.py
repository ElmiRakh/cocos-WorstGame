from gamestate import GameState


import sys
from time import sleep, localtime
from random import randint
from weakref import WeakKeyDictionary,getweakrefcount

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from simplejson import loads,dumps



class ServerChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		Channel.__init__(self, *args, **kwargs)
		self.id = str(self._server.NextId())
		self.state = self._server.GetState()

	def Close(self):
		self._server.DelPlayer(self)
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network_sendfleet(self, data):
		self._server.SendFleet(data['start'],data['target'])

	def Network_state(self,data):
		self._server.SendState()

	def Network_ready(self,data):
		self._server.AddReadyPlayer()


class GameServer(Server):
 
	channelClass = ServerChannel
	gamestate = GameState()
	
	pls = []

	PLNAMES = ['player1','player2']
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.id = 0
		self.state = self.gamestate.state
		self.players = WeakKeyDictionary()
		print ('Server launched')
	
	def NextId(self):
		self.id += 1
		return self.id

	def GetState(self):
		self.state = self.gamestate.state
		return self.state 
	
	def Connected(self, channel, addr):
		self.AddPlayer(channel)
		
	def AddPlayer(self, player):
		print ("New Player" + str(player.addr))
		print(self.pls)
		self.players[player] = True
		self.SendToAll({'action':'init',"state":self.GetState(),'players':self.id })

	def AddReadyPlayer(self):
		name = 'player{}'.format(len(list(self.players.keyrefs())))
		self.pls.append(name)
		print('PLAYERS',self.players)


	def SendState(self):
		self.SendToAll({'action':'state',"state": self.GetState() })
	
	def DelPlayer(self, player):
		print ("Deleting Player" + str(player.addr))
		del self.players[player]
		self.pls.pop()
		self.SendPlayers()
	
	def SendPlayers(self):
		self.SendToAll({"action": "players", "players": len(list(self.players.keyrefs()))})

	def SendFleet(self,start,target):
		self.gamestate.send_fleet(start,target)
	
	def SendToAll(self, data):
		[p.Send(data) for p in self.players]
	
	def Launch(self):
		time = 10
		while True:
			self.Pump()
			sleep(0.1)
			time += 1
			if len(list(self.players.keyrefs())) == 2:
				for i,p in enumerate(self.players):
					p.Send({'action':'nickname',"nickname": self.PLNAMES[i] })
				self.SendState()
				if time % 10 == 0:
					self.gamestate.update()
					self.GetState()
				print ("GAMESTATE update #" + str(time))
				

if __name__ == '__main__':
	host = '127.0.0.1'
	port = '7636'
	print ("STARTING SERVER ON LOCALHOST")
	gserve = GameServer(localaddr=(host, int(port)))
	gserve.Launch()
