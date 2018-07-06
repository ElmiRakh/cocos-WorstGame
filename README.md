# cocos-TestGame
It's a 2 player game made with python cocos2d and PodSixNet. It is aesthetically awful and has examples of worst coding practicies, yet works in relative degree. Architecture is quite basic - gamestate is on the server updates without relying on user and clients just request a updated state. It might have some educational value, in the sense of - "You shouldn't EVER code like THIS". 

To be serious, I put it here, because I couldn't find any examples of implemented cocos2d client-server games with state synchronization, when learning cocos2d. So, it might be useful if you find yourself at the same spot.  

# Dependencies
* pyglet
* cocos2d
* PodSixNet
* numpy
