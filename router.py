import time
import threading
import _thread
import math
import queue
import random

global hostList
hostList = list()
global linkList 
linkList = list()

global pktSize 
pktSize = 1000

class Router(object):
	def __init__(self,name,updateFreq):
		self.name = name
		self.routing_table = list()
		self.updateFreq = updateFreq
		return
		
	def init_setup(self,routing_table):
		for item in routing_table:
			self.routing_table.append(item)
		_thread.start_new_thread(self.routing_update,(self.updateFreq,))
		return
	
	def routing_update(self,updateFreq):
		while 1:
			time.sleep(updateFreq)
		return
	
	def route(self,pkt):
		#try:
		table_index = [y[0] for y in self.routing_table].index(pkt.dst)	
		#except ValueError:
		#	print('#','ERROR:',pkt.src,pkt.dst,pkt.pktNum,pkt.type)
		if self.routing_table[table_index][2] == 0:
			self.routing_table[table_index][1].onreceive(pkt,0)	
		else:
			self.routing_table[table_index][1].onreceive(pkt,1)	
		return
		
	def update_table(self,pkt):
		return
		
	def pkt_receive(self,pkt):
		#This should preferably be a constant delay function, since pkt_receive is in lockstep with link.propPkt. 
		print('#','Pkt received by router:',self.name,pkt.pktNum,'From:',pkt.src,'To:',pkt.dst)
		if pkt.type == 2:
			self.update_table(pkt)
		else:
			self.route(pkt)
		return