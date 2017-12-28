from collections import defaultdict,namedtuple
from simplejson import dumps,loads
import numpy as np
from constants import cost_matrix
from copy import deepcopy,copy

class GameState:
    
    def __init__(self,planets_num=7,npc_fleet=10,player_fleet=25,update_vel = 0.25,fleet_vel = 0.75,
                 cost_matrix = cost_matrix):
        self.cost_matrix = cost_matrix
        self.__state = self.initial_state(planets_num,npc_fleet,player_fleet)
        self.upd_dt = update_vel
        self.fl_dt = fleet_vel
        self.step = 1
        self.winner = None
        self.timer = {}

    @staticmethod    
    def initial_state(n,npc_f,player_f):
        Planet = namedtuple('Planet',['name','fleet','owner','target','attacked_by','supported_by','ett','start_step','active'])
        state = defaultdict(Planet)
        for pid in range(n):
            name = 'planet{}'.format(str(pid+1))
            if pid in [0,1]:
                owner = 'player{}'.format(str(pid+1))
                fleet = player_f                                       
            else:
                owner = 'neutral'
                fleet = npc_f
                
            target = name
            attacked_by = []
            supported_by = []
            p = Planet(name,fleet,owner,target,attacked_by,supported_by,0,0,False)
            state[name] = p
        return state
    
    # TODO method for initialisation of gameworld with arbitrary planet number.Should return locations
            
    @property
    def state(self):
        out = {name:dict(planet._replace(fleet=int(planet.fleet))._asdict()) for name,planet in self.__state.items()}
        out['step'] = self.step
        out['winner'] = self.winner
        return dumps(out)
    
    def get_estimated_time(self,start,dest,re=False):
        self.__state[start] = self.__state[start]._replace(start_step=self.step)
        if re:
            re_time = abs(self.step - getattr(self.__state[start],'start_step') - getattr(self.__state[start],'ett'))
            return self.cost_matrix[(start,dest)] + re_time
        else:
            return self.cost_matrix[(start,dest)]
        
    def send_fleet(self,start,dest):
        if dest == self.__state[start].target:
            return
        elif self.__state[start].target != start:
            self.cancel_action(start,self.__state[start].target)
        self.__state[start] = self.__state[start]._replace(target=dest)
        self.__state[start] = self.__state[start]._replace(ett=self.get_estimated_time(start,dest,re=False))
        self.set_timer(start)
        if self.__state[start].owner == self.__state[dest].owner:
            self.__state[dest].supported_by.append(start)
        else:
            self.__state[dest].attacked_by.append(start)
    
    def set_timer(self,planetname):
        self.timer[planetname] = self.step + self.__state[planetname].ett
        
    def check_timer(self):
        for name,time in self.timer.items():
            if self.step >= self.timer[name]:
                self.__state[name] = self.__state[name]._replace(active=True)
            
    def finish_action(self,planetname):
        self.__state[planetname] = self.__state[planetname]._replace(ett=0)
        self.__state[planetname] = self.__state[planetname]._replace(start_step=0)
        self.__state[planetname] = self.__state[planetname]._replace(active=False)
        
    def suspend_on_defeat(self,target):
        
        att_list =  copy(getattr(self.__state[target],'attacked_by'))
        sup_list = copy(getattr(self.__state[target],'supported_by'))
        candidates = att_list
        
        for attacker in att_list:
            self.cancel_action(attacker,target)
        for supporter in sup_list:
            self.cancel_action(supporter,target)

        new_owner = self.get_new_owner(candidates)
        self.__state[target] = self.__state[target]._replace(attacked_by = [])
        self.__state[target] = self.__state[target]._replace(supported_by = [])
        self.__state[target] = self.__state[target]._replace(target = target)
        self.__state[target] = self.__state[target]._replace(owner = new_owner)
        self.__state[target] = self.__state[target]._replace(fleet = 10)
        self.__state[target] = self.__state[target]._replace(ett = 0)
        self.__state[target] = self.__state[target]._replace(start_step = 0)
        self.__state[target] = self.__state[target]._replace(active = False)

    def get_new_owner(self,candidates):
        candidates_ = []
        for name in candidates:
            if self.__state[name].start_step + self.__state[name].ett >= self.step:
                candidates_.append(self.__state[name].owner)
        return np.random.choice(candidates_)

    def suspend_on_maxout(self,target):
        if self.__state[target].supported_by:
            for supporter in self.__state[target].supported_by:
                self.cancel_action(supporter,target)
        self.__state[target] = self.__state[target]._replace(supported_by=[])
        self.__state[target] = self.__state[target]._replace(fleet=100)
        
    def suspend_on_depletion(self,target):
        self.cancel_action(target,self.__state[target].target)
        self.__state[target] = self.__state[target]._replace(fleet = 1)
        self.__state[target] = self.__state[target]._replace(target = target)
        self.__state[target] = self.__state[target]._replace(active = False)        
        
            
            
    def cancel_action(self,start,dest):
        if self.__state[start].target != dest:
            return
        self.__state[start] = self.__state[start]._replace(start_step=self.step)
        self.__state[start] = self.__state[start]._replace(ett=self.get_estimated_time(start,dest,re=True))
        self.__state[start] = self.__state[start]._replace(target=start)
        if start in self.__state[dest].attacked_by:
            getattr(self.__state[dest],'attacked_by').remove(start)
            self.__state[dest] = self.__state[dest]._replace(attacked_by=self.__state[dest].attacked_by)
        elif start in self.__state[dest].supported_by:
            self.__state[dest].supported_by.remove(start)
            self.__state[dest] = self.__state[dest]._replace(supported_by=self.__state[dest].supported_by)
        else:
            raise Warning('Cancel action called with no candidate in destination')

    def calculate_neg_mod(self,planet):
        neg = 0
        for attacker in planet.attacked_by:
            if self.__state[attacker].active:
                neg+=1
        if planet.target != planet.name and planet.active: 
            neg+=1
        return neg
    
    def calculate_pos_mod(self,planet):
        pos = 0
        for supporter in planet.supported_by:
            if self.__state[supporter].active:
                pos+=1
        if planet.target == planet.name and planet.ett != 0:
            pos+=1
        if planet.owner != 'neutral':
            pos+=0.25
        return pos

    def check_win(self):
        owners = []
        for name,planet in self.__state.items():
            owners.append(planet.owner)
        if 'player1' not in owners:
            return 'player2'
        elif 'player2' not in owners:
            return 'player1'
        else:
            return None

    def update(self):
        self.step+=1
        changes = {}
        if self.check_win():
            self.winner = {'winner':self.check_win()}
            return
        for name,planet in self.__state.items():
            neg = self.calculate_neg_mod(planet)
            pos = self.calculate_pos_mod(planet)
            change = planet.fleet + self.upd_dt + self.fl_dt * pos - self.fl_dt * neg
            self.check_timer()
            if planet.target == planet.name and planet.ett != 0:
                if name in list(self.timer.keys()):
                    if planet.active:
                        self.finish_action(name)
            if change <= 0.2:
                if not planet.attacked_by:
                    self.suspend_on_depletion(name)
                else:
                    self.suspend_on_defeat(name)
            elif change >= 99.8:
                self.suspend_on_maxout(planet.name)
            else:
                self.__state[name] = self.__state[name]._replace(fleet=change)

######################################################################
####################            Tests              ###################
######################################################################
def test1():
	gs = GameState(planets_num=7,npc_fleet=10,player_fleet=25,update_vel = 0.1,fleet_vel = 0.25)
	gs.send_fleet('planet1','planet3')
	assert gs.state['planet3']['attacked_by'] == ['planet1']
	assert gs.state['planet1']['target'] == 'planet3'
	gs.send_fleet('planet2','planet3')
	assert gs.state['planet3']['attacked_by'] == ['planet1','planet2']
	assert gs.state['planet2']['target'] == 'planet3'

	for i in range(100):
		gs.update()
		
	assert gs.state['planet3']['attacked_by'] == []
	assert gs.state['planet1']['target'] == 'planet1'
	assert gs.state['planet2']['target'] == 'planet2'
	assert gs.state['planet2']['ett'] == 0
	assert gs.state['planet1']['ett'] == 0
	assert gs.state['planet3']['owner'] != 'neutral'
	print('Test 1 run successfully')
	
def test2():
	gs = GameState(planets_num=7,npc_fleet=10,player_fleet=25,update_vel = 0.1,fleet_vel = 0.25)
	gs.send_fleet('planet1','planet3')
	gs.send_fleet('planet2','planet3')
	for i in range(100):
		gs.update()
	if gs.state['planet3']['owner'] == gs.state['planet1']['owner']:
		gs.send_fleet('planet1','planet3')
		assert gs.state['planet3']['supported_by'] == ['planet1']
	else:
		gs.send_fleet('planet2','planet3')
		assert gs.state['planet3']['supported_by'] == ['planet2']
		
	for i in range(300):
		gs.update()
		
	assert gs.state['planet3']['supported_by'] == []
	assert gs.state['planet3']['fleet'] == 100
	print('Test 2 run successfully')

if __name__ == '__main__':
	test1()
	test2()


