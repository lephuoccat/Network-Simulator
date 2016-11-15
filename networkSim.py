import time
import _thread
import math
import queue
import random

#import matplotlib.pyplot as plt

#add router class
#check thoroughly for thread execution locks
#Talk to TA whether this "virtual" packet is fine or not.
global pktSize 
pktSize = 1000

class Packet:
	##################################################
	#				Packet contents				     #
	#SRC: Sender of the packet.					     #
	#DST: Destination of the packet.			     #
	#TYPE: Type of packet which can take three values#
	#	   0: denoting data packet                   #
	#      1: denoting ack 							 #
	#      2: denoting routing table update 		 #
	#PKTNUM: denotes the number of the packet sent.  #
	#        This number is local to each sender.	 #
	# <<<<<<<<<<<ADD MORE STUFF HERE>>>>>>>>>>>>	 #
	##################################################
	def __init__(self,src,dst,type,pktNum,size=pktSize): #TODO
		self.src = src
		self.dst = dst
		self.type = type
		self.pktNum = pktNum
		self.size = size
		
class Host(object):
	def __init__(self,name,timeout):
		self.pkt_num = 0
		self.name = name
		self.genDelay = 0.000001
		self.timeout = timeout
		##################################################################
		##retransmitPhase: one entry maintained for each destination.   ##
		##				   [0]: Is the flow in retransmit phase?        ##
		##				   [1]: The destination of the flow.			##
		##window:          one entry maintained per destination.        ##
		##                 [0]: The window size for the src-dst pair.   ##
		##                 [1]: The destination of the flow.            ##
		##lastAck:         one entry per destination.                   ##
		##                 [0]:#pkt for last ack received fron the dst. ##
		##                 [1]:The destination for the flow.            ##
		##                 [2]:#times ack for the last pkt is received. ##
		##lastPkt:         one entry per "active" packet.               ##
		##outstandingCnt:  one entry per destination                    ##
		##                 [0]: #unacknowledged packets for the src-dst ##
		##				   [1]: Corresponding dst for the flow.         ##
		##pktList:         one entry for each packet in flight.         ##
		##                 [0]:Time at which pkt was sent.              ##
		##                 [1]:Packet number of the packet.             ##
		##                 [2]:Destination of the packet.               ##
		##                 [3]:Size of the packet.                      ##
		##################################################################
		self.retransmitPhase = list()
		self.window = list()
		self.pktList = list()
		self.lastAck = list()
		self.lastPkt = list()
		self.outstandingCnt = list()
		self.pktLossCnt = 0		#improve this.
		_thread.start_new_thread(self.timeout_check,(self.timeout,))
		return
		
	#add link end specification	
	def link_setup(self,a,b):
		self.outgoing_link = a
		self.outgoing_link_type = b
		return 
	
	#Setup stuff for the flow. Creates a thread for flow_gen and returns immediately.
	def flow_init(self,delay,dst,size):
		try:
			idx = [y[1] for y in self.window].index(dst)
		except ValueError:
			#self.window.append([1,dst])
			self.window.append([30,dst])
			idx = len(self.window)-1
		t = _thread.start_new_thread(self.flow_gen,(delay,dst,size,idx))
		return 
		
	#Generates the packets of the flow.
	#Packet generation rate to depend on window here.
	def flow_gen(self,delay,dst,size,idx):
		time.sleep(delay)
		i = math.floor(size/pktSize)
		lastPktSize = size - i*pktSize
		try:
			outstandingCnt_idx = [y[1] for y in self.outstandingCnt].index(dst)
			retransmit_idx = [y[1] for y in self.retransmitPhase].index(dst)
			self.retransmitPhase[retransmit_idx][0] = 0
		except ValueError:
			self.outstandingCnt.append([0,dst])
			outstandingCnt_idx = len(self.outstandingCnt)-1
			self.retransmitPhase.append([0,dst])
			retransmit_idx = len(self.retransmitPhase)-1
			
		while i>0:
			while self.outstandingCnt[outstandingCnt_idx][0] >= self.window[idx][0] or self.retransmitPhase[retransmit_idx][0] == 1:
				time.sleep(0.0001)
			
			self.pkt_gen(0,dst,0,self.pkt_num,pktSize)
			self.pkt_num = self.pkt_num + 1
			self.pktList.append([time.time()-time_start,self.pkt_num,dst,size])
			self.outstandingCnt[outstandingCnt_idx][0] += 1
			i = i-1
			time.sleep(self.genDelay)
		if lastPktSize != 0:
			while self.outstandingCnt[outstandingCnt_idx][0] >= self.window[idx][0]:
				time.sleep(0.0001)
			self.pkt_gen(0,dst,0,self.pkt_num,lastPktSize)
			self.pktList.append([time.time()-time_start,self.pkt_num,dst,size])
			self.outstandingCnt[outstandingCnt_idx][0] += 1
			self.pkt_num = self.pkt_num + 1
		return
		
	def pkt_gen(self,delay,dst,type,pktNum,pktSize):
		time.sleep(delay)
		pkt = Packet(self.name,dst,type,pktNum)
		
		if pkt.type == 0:
			print('Packet number sent by host:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start),'window:',self.window,)
		else:
			print('Ack sent for packet number:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start),'window:',self.window,)
			
		if self.outgoing_link_type == 0:
			t = _thread.start_new_thread(self.outgoing_link.onreceive_dir0,(pkt,))	
		else:
			t = _thread.start_new_thread(self.outgoing_link.onreceive_dir1,(pkt,))	
		return 
		
	#retransmits the dropped pkt.
	def pkt_retransmit(self,pktNum,dst):
		retransmit_idx = [y[1] for y in self.retransmitPhase].index(dst)
		self.retransmitPhase[retransmit_idx][0] = 1
		
		outstandingCnt_idx = [y[1] for y in self.outstandingCnt].index(dst)
		idx = [y[1] for y in self.window].index(dst)
		
		self.outstandingCnt[outstandingCnt_idx][0] = 0
		while self.outstandingCnt[outstandingCnt_idx][0] >= self.window[idx][0]:
			time.sleep(0.0001)
		
		idx1 = 	[[y[2],y[3]] for y in self.pktList].index([pktNum,dst])
		self.pkt_gen(0,dst,0,nextPkt,self.pktList[idx1][3])
		self.pktList[idx1][0] = time.time()-time_start
		self.outstandingCnt[outstandingCnt_idx][0] += 1
		nextPkt += 1
		self.retransmitPhase[retransmit_idx][0] = 0
		return
		
	def detect_pkt_loss(self,pktNum,src):
		try: 
			index = [y[1] for y in self.lastAck].index(src)
			if pkt.pktNum == self.lastAck[index][0]:
				self.lastAck[index][2] += 1
				if self.lastAck[index][2] == 3:
					self.change_window(1,src)
					self.pktLossCnt += 1		#improve this.
					_thread.start_new_thread(self.pkt_retransmit,(pktNum+1,src))
			else if pkt.pktNum > self.lastAck[index][0]:
				self.change_window(0,src)
				self.lastAck[index][0] += 1
				self.lastAck[index][2] = 1
				pktIndex = [y[3] for y in self.pktList].index(src)
				self.pktList.pop(pktIndex)
				
		except ValueError:
				self.change_window(0,src)
				self.lastPkt.append([pktNum,src,1])
				
		return
		
	def pkt_receive(self,pkt):
	#Figure out way to deal with trailing end of the simulation.
	#A thread should have a lock on self.lastPkt.append at any given time. Need to serialize execution of threads there.
	#Issue with ordering of acks otherwise.
	#Send ack for last packet received w/o pkt loss.
		if pkt.type == 0:
			print('Packet number received by host:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start),'window:',self.window,)
			if len(self.lastPkt) != 0:
				self.lastPkt.append(pkt.pktNum)
				self.lastPkt.sort()	
				if self.lastPkt[1] == self.lastPkt[0]+1:
					ackNum = self.lastPkt[1]
					self.lastPkt.remove(ackNum-1)
				else:
					ackNum = self.lastPkt[0]
			else:
				self.lastPkt.append(pkt.pktNum)
				ackNum = pkt.pktNum
			t = _thread.start_new_thread(self.pkt_gen,(2,pkt.src,1,ackNum,64))
		else:
			self.detect_pkt_loss(pkt.pktNum,pkt.src)
			print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start),'window:',self.window,)
			outstandingCnt_idx = [y[1] for y in self.outstandingCnt].index(pkt.src)
			self.outstandingCnt[outstandingCnt_idx][0] -= 1
		return
	
	#This changes according to the congestion control algorithm.
	#Currently TCP Reno is implemented.
	def change_window(self,isLoss,src):
		i = [y[1] for y in self.window].index(src)
		if isLoss:
			#self.window[i][0] = math.ceil(self.window[i][0]/2)
			self.window[i][0] = self.window[i][0] 
		else:
			self.window[i][0] = self.window[i][0] 
			#self.window[i][0] = self.window[i][0] + 1
		return
		
	#Add timeout mechanism
	def timeout_check(self,timeout):
		for i in range(len(self.pktList)):
			if self.pktList[i][0] - (time.time()-time.start) >= timeout:
				self.pkt_gen(0,self.pktList[i][2],0,self.pktList[i][1],self.pktList[i][3])
				self.pktList[i][0] = time.time()-time.start
				idx = [y[1] for y in self.window].index(self.pktList[i][2])
				self.window[idx][0] = 1
		return

class Router(object):
	def __init__(self,name,updateFreq):
		self.name = name
		self.routing_table = list()
		self.updateFreq = updateFreq
		return
		
	def init_setup(self,routing_table):
		############Routing Table structure:##############
		## |-----------|--------------|----------------|##
		## |    dst    |    link      |     link-end   |##
		## |-----------|--------------|----------------|##
		##################################################
		for item in routing_table:
			self.routing_table.append(item)
		_thread.start_new_thread(self.routing_update,(self.updateFreq,))
		return
	
	def routing_update(self,updateFreq):
		while 1:
			time.sleep(updateFreq)
		return
	
	def route(self,pkt):
		table_index = [y[0] for y in self.routing_table].index(pkt.dst)	
		if self.routing_table[table_index][2] == 0:
			t = _thread.start_new_thread(self.routing_table[table_index][1].onreceive_dir0,(pkt,))	
		else:
			t = _thread.start_new_thread(self.routing_table[table_index][1].onreceive_dir1,(pkt,))	
		return
		
	def update_table(self,pkt):
		return
		
	def pkt_receive(self,pkt):
		print('Pkt received by router:',self.name,pkt.pktNum,'From:',pkt.src,'To:',pkt.dst)
		if pkt.type == 2:
			self.update_table(pkt)
		else:
			self.route(pkt)
		return
		
class Buffer(object):
	def __init__(self, size, link):
		self.available_space = size
		self.link = link
		self.queue = queue.Queue()
		self.drop_pkt = 0
		self.itemsPut = 0
		self.itemsPop = 0
		return

	#place a packet in the buffer if there is space
	#drop the packet if space== 0
	def put(self, packet, destination):
		if self.available_space >= packet.size:
			self.queue.put_nowait((packet, destination))
			self.available_space -= packet.size
			self.itemsPut += 1
		else:
			print('Packet dropped:',packet.pktNum)
			self.drop_pkt += 1
            
	#retrieve the next packet from the buffer in order.
	def get(self):
		(packet, destination) = self.queue.get_nowait()
		self.available_space += packet.size
		self.itemsPop += 1
		return (packet, destination)
        
        
class biDirectionalLink(object):
	#figure out something for queue ends. Behaviour depends on which queue end packet came from.
	def __init__(self,a,b,src,dst,size,name,start_delay):
		self.rate = a
		self.propDelay = b
		self.src_dir0 = src
		self.dst_dir0 = dst
		self.src_dir1 = dst
		self.dst_dir1 = src
		self.name = name
		self.buffer_0 = Buffer(size, self)
		self.buffer_1 = Buffer(size, self)
		self.channel0Active = 1
		self.channel1Active = 0
		self.t0_start = time.time()
		self.t1_start = 0
		self.start_delay = start_delay;
		_thread.start_new_thread(self.activeChannel,(self.start_delay,))
		_thread.start_new_thread(self.sendPkt,())
		return
		
	def  activeChannel(self,start_delay):
		##switches between channels based on some arbitration scheme.
		T = 5
		poll_delay = 0.00001
		time.sleep(start_delay)
		while 1:
			time.sleep(poll_delay)
			if self.channel0Active == 1:
				if (time.time() - self.t0_start >= T) or (self.buffer_0.itemsPut - self.buffer_0.itemsPop == 0 and self.buffer_1.itemsPut - self.buffer_1.itemsPop != 0):
					print(self.name,'Channel switch',(int)(time.time()-time_start),)
					self.t1_start = time.time()
					self.channel0Active  = 0
					self.channel1Active  = 1
			else:
				if (time.time() - self.t1_start >= T) or (self.buffer_1.itemsPut - self.buffer_1.itemsPop == 0 and self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0):
					print(self.name,'Channel switch',(int)(time.time()-time_start),)
					self.t0_start = time.time()
					self.channel0Active  = 1
					self.channel1Active  = 0
		return
		
	def propPkt(self,pkt, dst):
		#propagates the pkt through the link with propDelay delay.
		time.sleep(self.propDelay)
		dst.pkt_receive(pkt)
		return 
		
	def sendPkt(self):
		## pull out packets from the queues depending on whether channel is active or not.
		## sleep for transDelay.
		## spawn process for propPkt
		while 1:
			if self.channel0Active == 1:
				#print(self.name,':Channel 0 active',(int)(time.time()-time_start))
				if self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0:
					(pkt, dst) = self.buffer_0.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					_thread.start_new_thread(self.propPkt,(pkt,dst))
				else:
					time.sleep(0.00001)
			if self.channel1Active == 1:
				#print(self.name,':Channel 1 active',(int)(time.time()-time_start))
				if self.buffer_1.itemsPut - self.buffer_1.itemsPop != 0:
					(pkt, dst) = self.buffer_1.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					_thread.start_new_thread(self.propPkt,(pkt,dst))
				else:
					time.sleep(0.00001)
		return
		
	def onreceive_dir0(self,pkt):
		#print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		self.buffer_0.put(pkt,self.dst_dir0)
		return
		
	def onreceive_dir1(self,pkt):
		#print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		self.buffer_1.put(pkt,self.dst_dir1)
		return

class uniDirectionalLink(object):
	def __init__(self,a,b,src,dst,size,name):
		self.transDelay = a
		self.propDelay = b
		self.src = src
		self.dst = dst
		self.name = name
		self.bufSize = size
	
	def onreceive(self,pkt):
		print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		time.sleep(self.transDelay+self.propDelay)
		t = _thread.start_new_thread(self.dst.pkt_receive,(pkt,))
		return
		
def test0():
	#Host initialization.
	H1 = Host('H1',30)
	H2 = Host('H2',30)
		
	#Link Initialization.
	L1 = biDirectionalLink((10e6)/8,0.01,H1,H2,32*(10e2),'L1',0)
		
	#Link setup for hosts.
	H1.link_setup(L1,0)
	H2.link_setup(L1,1)
		
	#Start of simulation.
	global time_start
	time_start = time.time()
	H1.flow_init(1.0,'H2',20*(10e5))	
	time.sleep(1500)
	return
		
def test1():
	#Host initialization.
	H1 = Host('H1',30)			#30: Timeout time (in s)
	H2 = Host('H2',30)
		
	#Router initialization.
	R1 = Router('R1',10)		#10: Routing Table update freq (in s)
	R2 = Router('R2',10)
	R3 = Router('R3',10)
	R4 = Router('R4',10)
		
	#Link initialization.
	L0 = biDirectionalLink(0.125*12.5*10e5,0.01,H1,R1,32*10e2,'L0',0)  
	L1 = biDirectionalLink(0.125*10*10e5,0.01,R1,R2,32*10e2,'L1',1)
	L2 = biDirectionalLink(0.125*10*10e5,0.01,R1,R3,32*10e2,'L2',0.5)
	L3 = biDirectionalLink(0.125*10*10e5,0.01,R2,R4,32*10e2,'L3',2)
	L4 = biDirectionalLink(0.125*10*10e5,0.01,R3,R4,32*10e2,'L4',3)
	L5 = biDirectionalLink(0.125*12.5*10e5,0.01,R4,H2,32*10e2,'L5',2.6)
		
	#outgoing link end specification for hosts
	H1.link_setup(L0,0)
	H2.link_setup(L5,1)
		
	#Routing tables for the routers.
	R1.init_setup([['H2',L1,0],['H1',L0,1]]);
	R2.init_setup([['H2',L3,0],['H1',L1,1]]);
	R3.init_setup([['H2',L4,0],['H1',L2,1]]);
	R4.init_setup([['H2',L5,0],['H1',L4,1]]);
		
	#Start of simulation.
	global time_start
	time_start = time.time()
	H1.flow_init(0.5,'H2',20*10e5)	
	time.sleep(1500)
	return
		
def test_own():
	H1 = Host('H1',30)
	H2 = Host('H2',30)
	R = Router('R',10)
	L1 = biDirectionalLink(1000000,3,H1,R,32000,'L1',0)   # ASK TA about 32 or 64
	L2 = biDirectionalLink(1000000,3,R,H2,32000,'L2',5)
	#only specify the outgoing link side.
	H1.link_setup(L1,0)
	H2.link_setup(L2,1)
	RoutingTable = [['H1',L1,1],['H2',L2,0]]
	R.init_setup(RoutingTable)
	
	global time_start
	time_start = time.time()
	H1.flow_init(0.5,'H2',10000)	
	H2.flow_init(0,'H1',5000)
	#figure out better way to do this. Check for end of all threads
	time.sleep(30)	
	return
		
test1()