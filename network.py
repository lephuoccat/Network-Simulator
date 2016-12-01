import time
import threading
import _thread
import math
import queue
import random
#import matplotlib.pyplot as plt

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
		######################################################################
		##The host class creates flows, sends packets to the required links,##
		##performs packet retransmissions due to packet loss or timeouts,   ##
		##generates acknowledgements for received packets & does congestion ##
		##control.                                                          ##
		##The host class can handle simultaneously packets from one src/dst ##
		##only. That is okay for our current simulation purposes.           ##
		######################################################################
	def __init__(self,name,timeout,algo):
		self.pkt_num = 0
		self.name = name
		self.genDelay = 0.000001
		self.timeout = timeout
		#####################################################################
		##sstart:		   Is the flow for this source in slow start phase?##
		##retransmitPhase: Is the flow for this source in retransmit phase?##   
		##				   Enforces an interlock which allows either       ##
		##				   retransmitted packets or new packets to be sent.##
		##window:          The window size for the flow (only one flow     ##
		##                 allowed at a time for a source).                ##
		##recAckQueue:	   A sorted list of ack's received by the host.    ##
		##				   [0]:The pktNum for which the ack was received.  ##
		##				   [1]:The number of times the ack was received.   ##
		##				   [2]:The number of times the ack can be retransm-##
		##                 itted before triggering a packet loss.          ##
		##recPktQueue:     Sorted list of data packets received by the host## 
		##pktLost:		   [0]:The lost packet that is being retransmitted.##
		##				   [1]:Num of times the pkt has to be retransmitted##
		##outstandingCnt:  The number of outstanding packets in flight.    ##
		##pktList:         one entry for each packet in flight.            ##
		##                 [0]:Time at which pkt was sent.                 ##
		##                 [1]:Packet number of the packet.                ##
		##                 [2]:Destination of the packet.                  ##
		##                 [3]:Size of the packet.                         ##
		#####################################################################
		self.sstart = 0
		self.retransmitPhase = 0
		self.window = 50
		self.pktList = list()
		self.recAckQueue = list()
		self.recPktQueue = list()
		self.pktLost = list()
		self.outstandingCnt = 0
		self.pktLossCnt = 0
		self.flowSrc = ''
		self.flowDst = ''
		self.firstAck = 0
		self.base_RTT = 0
		self.curr_RTT = 0
		self.lastAckSent = -1
		self.congestionAlgo = algo
		self.pktListLock = threading.RLock()
		self.recPktLock = threading.RLock()
		self.recAckLock = threading.RLock()
		self.windowChangeLock = threading.RLock()
		
		_thread.start_new_thread(self.timeout_check,(self.timeout,))
		_thread.start_new_thread(self.pkt_retransmit,(self.flowDst,))
		return
		
	#sets up the name and the end type of the outgoing link for the host.
	def link_setup(self,a,b):
		self.outgoing_link = a
		self.outgoing_link_type = b
		return 
	
	#Initial setup for the flow. Flows start off in slow start with a window size
	#of 1, and a variable delay before packet transmission starts.
	def flow_init(self,delay,dst,size):
		self.window = 1
		self.sstart = 1
		t = _thread.start_new_thread(self.flow_gen,(delay,dst,size))
		return 
		
	#Generates the packets for the flow, with the appropriate packet number & size.
	#Adds in each generated packet into pktList.
	def flow_gen(self,delay,dst,size):
		time.sleep(delay)
		self.flowDst = dst
		i = math.floor(size/pktSize)
		lastPktSize = size - i*pktSize
		while i>0:
			while self.outstandingCnt >= self.window or self.retransmitPhase == 1:
				time.sleep(0.001)
			print('i',i,'Time',time.time()-time_start,'Control passed over to flow_gen')
			self.pkt_gen(0,dst,0,self.pkt_num,pktSize)
			self.pkt_num = self.pkt_num + 1
			
			self.pktListLock.acquire(1)
			try:
				self.pktList.append([time.time()-time_start,self.pkt_num,dst,pktSize])
				#print('Append: Pkt list:',[y[1] for y in self.pktList])
				self.outstandingCnt += 1
			finally:
				self.pktListLock.release()
			
			i = i-1
			time.sleep(self.genDelay)
		if lastPktSize != 0:
			while self.outstandingCnt >= self.window:
				time.sleep(0.0001)
			self.pkt_gen(0,dst,0,self.pkt_num,lastPktSize)
			
			self.pktListLock.acquire(1)
			try:
				self.pktList.append([time.time()-time_start,self.pkt_num,dst,lastPktSize])
				self.outstandingCnt += 1
			finally:
				self.pktListLock.release()
			
			self.pkt_num = self.pkt_num + 1
		print('ALL PACKETS SENT:',self.pkt_num)
		return
		
	#Generates packet with size=pktSize & packet number=pktNum. Sends generated packet to 
	#the outgoing link.
	def pkt_gen(self,delay,dst,type,pktNum,pktSize):
		time.sleep(delay)
		pkt = Packet(self.name,dst,type,pktNum,pktSize)
		
		if pkt.type == 0:
			print('Packet number sent by host:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
		else:
			print('Ack sent for packet number:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
		
		if self.outgoing_link_type == 0:
			self.outgoing_link.onreceive(pkt,0)	
		else:
			self.outgoing_link.onreceive(pkt,1)	
		return 
		
	#Retransmits a dropped packet. It waits for the acknowledgement of the packet
	#to arrive before passing over control to flow_gen for transmission of the remaining
	#packets.
	def pkt_retransmit(self,dst):
		retransmitList = list()
		restart = 0
		ackReceived = 0
		
		while 1:
			if len(self.pktLost) != 0:
				print('Pkt lost list:',self.pktLost)
				for i in range(len(self.pktLost)):
					retransmit = 0
					if restart == 1:
						i = max(0,i-1)
						restart = 0
					try:
						idx = [y[0] for y in retransmitList].index(self.pktLost[i][0])
						if retransmitList[idx][1] < self.pktLost[i][1]:
							retransmit = 1
							currPkt = self.pktLost[i][0]
							retransmitNum = self.pktLost[i][1]
							retransmitList[idx][1] += 1
					except ValueError:
						retransmit = 1
						currPkt = self.pktLost[i][0]
						retransmitNum = self.pktLost[i][1]
						retransmitList.append([self.pktLost[i][0],1])
					
					if retransmit == 1:
						self.retransmitPhase = 1
						print('RETRANSMIT PHASE STARTED')
						while self.outstandingCnt >= self.window:
							time.sleep(0.0001)
						try:
							k = [y[1] for y in self.pktList].index(currPkt)
							self.pkt_gen(0,dst,0,self.pktList[k][1],self.pktList[k][3])
							self.pktList[k][0] = time.time()-time_start
							self.outstandingCnt += 1
							print('Packet retransmitted:',self.pktList[k][1])
						except ValueError:
							pass	
							
						while 1:
							try:
								m = [y[0] for y in self.pktLost].index(currPkt)
								if self.pktLost[m][1] > retransmitNum:
									restart = 1
									break
							except ValueError:
								ackReceived = 1
								self.retransmitPhase = 0
								print('RETRANSMIT PHASE ENDED')
								break
							time.sleep(0.0001)
							
					if ackReceived == 1:
						ackReceived = 0
						break
					time.sleep(0.001)
			else:
				time.sleep(0.001)
		return
	
	#Detects packet loss based on the number of duplicate acks received. 
	#Updates recAckQueue to remove all unnecessary acks (all acks with a lower number
	#than the current ack possess redundant information). 
	#Calls change_window to implement the congestion control algorithm.	
	def detect_pkt_loss(self,pktNum,src):
		isPktLoss = 0
		retransmit_idx = 0
		
		self.recAckLock.acquire(1)
		try:
			try:
				idx = [y[0] for y in self.recAckQueue].index(pktNum)
				if self.recAckQueue[idx][1] >= self.recAckQueue[idx][2]:
					print('PKT LOSS DETECTED','Time:',"%0.2f" % (time.time()-time_start))
					isPktLoss = 1
					try: 
						k = [y[0] for y in self.pktLost].index(pktNum)
						self.pktLost[k][1] += 1
					except ValueError:
						self.pktLost.append([pktNum+1,1])
					
					retransmit_idx = self.recAckQueue[idx][0]
					self.recAckQueue[idx][2] = self.pktList[len(self.pktList)-1][1]-self.recAckQueue[idx][0]+3
				else:
					self.recAckQueue[idx][1] += 1
			except ValueError:
				i = [y[0] for y in self.recAckQueue if y[0] <= pktNum]
				if len(i) == len(self.recAckQueue):
					self.recAckQueue.append([pktNum,1,4])
					self.recAckQueue.sort()
		
			self.change_window(isPktLoss,src)
			
			del_idx = [i for i in range(len(self.recAckQueue)) if self.recAckQueue[i][0] < pktNum]
			for j in sorted(del_idx, reverse = True):
				del self.recAckQueue[j]
		
			print('recAckQueue',self.recAckQueue,'Time:',"%0.2f" % (time.time()-time_start))
		
		finally:
			self.recAckLock.release()
		
		return
	
	#If a data packet is received, sends ack for the last packet received in-order.
	#Removes all packets with a pktNum less than the ack received from the pktList queue, since they are no longer 'active'
	#If an ack is received, triggers detect_pkt_loss for checking for packet losses & for congestion control.
	def pkt_receive(self,pkt):
		last_inorder_idx = 0
		if pkt.type == 0:
			self.recPktLock.acquire(1)
			try:
				if self.flowSrc == '':
					self.flowSrc = pkt.src
				
				print('Packet number received by host:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
			
				try:
					idx = self.recPktQueue.index(pkt.pktNum)
				except ValueError:
					if pkt.pktNum > self.lastAckSent:
						self.recPktQueue.append(pkt.pktNum)
				if len(self.recPktQueue) != 0:
					self.recPktQueue.sort()	
			
				print('recPktQueue:',self.recPktQueue)
				for i in range(len(self.recPktQueue)):
					if i == len(self.recPktQueue) - 1:
						last_inorder_idx = i
					elif (self.recPktQueue[i+1] != self.recPktQueue[i]+1):
						last_inorder_idx = i
						break
	
				ackNum = self.recPktQueue[last_inorder_idx]
			
				if last_inorder_idx != 0:
					del self.recPktQueue[0:last_inorder_idx-1]
				self.lastAckSent = ackNum
				self.pkt_gen(0,pkt.src,1,ackNum,64)
				self.lastAckTime = time.time()
			finally:
				self.recPktLock.release()
			
		else:
			print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
			if self.outstandingCnt > 0:
				self.outstandingCnt -= 1
			
			try:
				idx1 = [i for i in range(len(self.pktLost)) if self.pktLost[i][0] <= pkt.pktNum]
				for i in sorted(idx1, reverse=True):
					del self.pktLost[i]
			except ValueError:
				pass
			self.pktListLock.acquire(1)
			try:
				try:
					idx1 = [y[1] for y in self.pktList].index(pkt.pktNum)
					self.curr_RTT = time.time() - time_start - self.pktList[idx1][0]
					idx = [i for i in range(len(self.pktList)) if self.pktList[i][1] <= pkt.pktNum]
					for i in sorted(idx, reverse=True):
						del self.pktList[i]
				except ValueError:
					pass
				
				if self.firstAck == 0:
					self.firstAck = 1
					self.base_RTT = self.curr_RTT
				else:
					if self.curr_RTT < self.base_RTT:
						self.base_RTT = self.curr_RTT
						
				self.detect_pkt_loss(pkt.pktNum,pkt.src)
				print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,'outstandingCnt',self.outstandingCnt)
			
			finally:
				self.pktListLock.release()
		return
	
	#Implements the congestion control mechanism.
	#Changes the window size depending on state(slow start/congestion avoidance) and on whether a packet loss occurred.
	def change_window(self,pktLoss,src):
		self.windowChangeLock.acquire(1)
		try:
			if self.congestionAlgo == 'RENO':
				if pktLoss:
					self.window = math.floor(self.window/2)
					self.sstart = 0
				else:
					if self.sstart == 1:
						self.window = self.window + 1
					else:
						self.window = self.window + 1/self.window
			else:
				if pktLoss:
					self.sstart = 0
				else:
					if self.sstart:
						self.window = self.window + 1
					else:
						self.window = min(2*self.window, gamma*(self.base_RTT/self.curr_RTT * self.window + alpha)+(1-gamma)*self.window)
		finally:
			self.windowChangeLock.release()
		return
		
	#Checks for packet timeout periodically. The timeout period can be set by the user.
	#On detecting a timeout, retransmits the timed-out packet, and reduces window size to 1.
	#Changes the timestamp (sending time) of all subsequent packets to the current time,
	#so that all subsequent packets don't time out immediately.
	def timeout_check(self,timeout):
		while 1:
			for y in self.pktList:
				if time.time()-time_start - y[0] >= timeout:
					try:
						isLost = [y[0] for y in self.pktLost].index(y[1])
					except ValueError:
						print('Timeout occured')
						self.pktListLock.acquire(1)
						try:
							self.pkt_gen(0,y[2],0,y[1],y[3])
							for l in self.pktList:
								if l[1] >= y[1]:
									l[0] = time.time()-time_start
							self.outstandingCnt = 1
						finally:
							self.pktListLock.release()
					
						self.windowChangeLock.acquire(1)
						try:
							self.sstart = 1
							self.window = 1
						finally:
							self.windowChangeLock.release()
					
						time.sleep(RTT)
						print('Timeout: Pkt retransmitted:',y[1],'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window)
						break
			time.sleep(0.001)
		return

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
		table_index = [y[0] for y in self.routing_table].index(pkt.dst)	
		if self.routing_table[table_index][2] == 0:
			self.routing_table[table_index][1].onreceive(pkt,0)	
		else:
			self.routing_table[table_index][1].onreceive(pkt,1)	
		return
		
	def update_table(self,pkt):
		return
		
	def pkt_receive(self,pkt):
		#This should preferably be a constant delay function, since pkt_receive is in lockstep with link.propPkt. 
		print('Pkt received by router:',self.name,pkt.pktNum,'From:',pkt.src,'To:',pkt.dst)
		if pkt.type == 2:
			self.update_table(pkt)
		else:
			self.route(pkt)
		return
		
class Buffer(object):
	def __init__(self, size, name):
		self.available_space = size
		self.queue = list()
		self.drop_pkt = 0
		self.itemsPut = 0
		self.itemsPop = 0
		self.name = name
		self.queueLock = threading.RLock()
		return

	#place a packet in the buffer if there is space
	#drop the packet if space== 0
	def put(self, packet, destination):
		self.queueLock.acquire(1)
		try:
			if self.available_space >= packet.size:
				self.queue.append((packet, destination))
				self.available_space -= packet.size
				self.itemsPut += 1
			else:
				print('Packet dropped:',packet.pktNum,packet.type)
				self.drop_pkt += 1
		finally:	
			self.queueLock.release()
		return
		
	#retrieve the next packet from the buffer in order.
	def get(self):
		self.queueLock.acquire()
		try:
			(packet, destination) = self.queue.pop(0)
			self.available_space += packet.size
			self.itemsPop += 1
		finally:	
			self.queueLock.release()
		
		return (packet, destination)
        
class biDirectionalLink(object):
	def __init__(self,a,b,src,dst,size,name,start_delay):
		self.rate = a
		self.propDelay = b
		self.src_dir0 = src
		self.dst_dir0 = dst
		self.src_dir1 = dst
		self.dst_dir1 = src
		self.name = name
		self.buffer_0 = Buffer(size, self.name+'Buf_0')
		self.buffer_1 = Buffer(size, self.name+'Buf_1')
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
					self.t1_start = time.time()
					self.channel0Active  = 0
					self.channel1Active  = 1
			else:
				if (time.time() - self.t1_start >= T) or (self.buffer_1.itemsPut - self.buffer_1.itemsPop == 0 and self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0):
					self.t0_start = time.time()
					self.channel0Active  = 1
					self.channel1Active  = 0
		return
		
	def propPkt(self,pkt, dst):
		#propagates the pkt through the link with propDelay delay.
		#pkt_receive of both hosts and routers should be constant delay functions.
		time.sleep(self.propDelay)
		dst.pkt_receive(pkt)
		return 
		
	def sendPkt(self):
		while 1:
			if self.channel0Active == 1:
				#print(self.name,':Channel 0 active',"%0.2f" % (time.time()-time_start))
				if self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0:
					(pkt, dst) = self.buffer_0.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					_thread.start_new_thread(self.propPkt,(pkt,dst))
				else:
					time.sleep(0.00001)
			if self.channel1Active == 1:
				#print(self.name,':Channel 1 active',"%0.2f" % (time.time()-time_start))
				if self.buffer_1.itemsPut - self.buffer_1.itemsPop != 0:
					(pkt, dst) = self.buffer_1.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					print('Before thread start')
					_thread.start_new_thread(self.propPkt,(pkt,dst))
					print('thread started')
				else:
					time.sleep(0.00001)
		return
		
	def onreceive_dir0(self,pkt):
		self.buffer_0.put(pkt,self.dst_dir0)
		print('Channel 0 active:',self.channel0Active)
		return
		
	def onreceive_dir1(self,pkt):
		self.buffer_1.put(pkt,self.dst_dir1)
		return

class biDirectionalLinkv2(object):
	def __init__(self,a,b,src,dst,size,name):
		self.rate = a
		self.propDelay = b
		self.src_dir0 = src
		self.dst_dir0 = dst
		self.src_dir1 = dst
		self.dst_dir1 = src
		self.name = name
		self.buffer = Buffer(size, self.name+'Buf')
		_thread.start_new_thread(self.sendPkt,())
		return
		
	def propPkt(self,pkt, dst):
		time.sleep(self.propDelay)
		dst.pkt_receive(pkt)
		return 
		
	def sendPkt(self):
		while 1:
			if len(self.buffer.queue)!=0:
				(pkt, dst) = self.buffer.get()
				transmission_delay = pkt.size / self.rate
				time.sleep(transmission_delay)
				_thread.start_new_thread(self.propPkt,(pkt,dst))
			else:
				time.sleep(0.0001)
		return
		
	def onreceive(self,pkt,dir):
		if dir == 0:
			self.buffer.put(pkt,self.dst_dir0)
		else:
			self.buffer.put(pkt,self.dst_dir1)
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
		print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start))
		time.sleep(self.transDelay+self.propDelay)
		t = _thread.start_new_thread(self.dst.pkt_receive,(pkt,))
		return

def variable_poll():
	window_size = 0
	buf_occupancy = 0
	flow_rate = 0
	packet_loss  = 0
	packet_delay = 0
	link_rate = 0
	while 1:
		window_size = H1.window
		buf_occupancy = 1 - L1.buffer.available_space/(64000)
		flow_rate = 0
		packet_loss  = 0
		packet_delay = H1.curr_RTT - H1.base_RTT
		link_rate = 0
		time.sleep(0.01)
	return

	
def test0():
	#Host initialization.
	global RTT
	RTT = 0.04
	global H1
	H1 = Host('H1',200*RTT,'RENO')
	global H2
	H2 = Host('H2',200*RTT,'RENO')
		
	#Link Initialization.
	global L1
	#L1 = biDirectionalLink((10e6)/8,0.01,H1,H2,32*(10e2),'L1',0)
	L1 = biDirectionalLinkv2((10e6)/8,0.01,H1,H2,64*(10e2),'L1')
		
	#Link setup for hosts.
	H1.link_setup(L1,0)
	H2.link_setup(L1,1)
		
	global alpha
	alpha = 15
	global gamma
	gamma = 0.5
	#Start of simulation.
	global time_start
	time_start = time.time()

	#t = _thread.start_new_thread(variable_poll_test0,())
	
	H1.flow_init(1.0,'H2',20*(10e4))	
	time.sleep(70)
	return
		
def test1():
	global RTT
	RTT = 0.06
	
	#Host initialization.
	global H1
	H1 = Host('H1',RTT*150)			
	global H2
	H2 = Host('H2',RTT*150)
		
	#Router initialization.
	global R1
	R1 = Router('R1',10)		#10: Routing Table update freq (in s)
	global R2
	R2 = Router('R2',10)
	global R3
	R3 = Router('R3',10)
	global R4
	R4 = Router('R4',10)
		
	#Link initialization.
	global L0
	L0 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,H1,R1,64*10e2,'L0')  
	global L1
	L1 = biDirectionalLinkv2(0.125*10*10e5,0.01,R1,R2,64*10e2,'L1')
	global L2
	L2 = biDirectionalLinkv2(0.125*10*10e5,0.01,R1,R3,64*10e2,'L2')
	global L3
	L3 = biDirectionalLinkv2(0.125*10*10e5,0.01,R2,R4,64*10e2,'L3')
	global L4
	L4 = biDirectionalLinkv2(0.125*10*10e5,0.01,R3,R4,64*10e2,'L4')
	global L5
	L5 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,R4,H2,64*10e2,'L5')
		
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

	t = _thread.start_new_thread(variable_poll,())

	H1.flow_init(0.5,'H2',20*(10e4))	
	time.sleep(130)
	return
	
def test2():
	global RTT
	RTT = 0.06
	
	#Host initialization.
	global S1
	S1 = Host('S1',RTT*150)	
	global S2
	S2 = Host('S2',RTT*150)
	global S3
	S3 = Host('S3',RTT*150)	
	global T1
	T1 = Host('T1',RTT*150)	
	global T2
	T2 = Host('T2',RTT*150)	
	global T3
	T3 = Host('T3',RTT*150)		
		
	#Router initialization.
	global R1
	R1 = Router('R1',10)		#10: Routing Table update freq (in s)
	global R2
	R2 = Router('R2',10)
	global R3
	R3 = Router('R3',10)
	global R4
	R4 = Router('R4',10)
		
	#Link initialization.
	global L0
	L0 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,S2,R1,128*10e2,'L0')  
	global L1
	L1 = biDirectionalLinkv2(0.125*10*10e5,0.01,R1,R2,128*10e2,'L1')
	global L2
	L2 = biDirectionalLinkv2(0.125*10*10e5,0.01,R2,R3,128*10e2,'L2')
	global L3
	L3 = biDirectionalLinkv2(0.125*10*10e5,0.01,R3,R4,128*10e2,'L3')
	global L4
	L4 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,S1,R1,128*10e2,'L4')
	global L5
	L5 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,R2,T2,128*10e2,'L5')
	global L6
	L6 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,S3,R3,128*10e2,'L5')
	global L7
	L7 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,R4,T1,128*10e2,'L5')
	global L8
	L8 = biDirectionalLinkv2(0.125*12.5*10e5,0.01,R4,T3,128*10e2,'L5')
		
	#outgoing link end specification for hosts
	S1.link_setup(L4,0)
	S2.link_setup(L0,0)
	S3.link_setup(L6,0)
	T1.link_setup(L7,1)
	T2.link_setup(L5,1)
	T3.link_setup(L8,1)
		
	#Routing tables for the routers.
	R1.init_setup([['S1',L4,1],['S2',L0,1],['S3',L1,0],['T1',L1,0],['T2',L1,0],['T3',L1,0]]);
	R2.init_setup([['S1',L1,1],['S2',L1,1],['S3',L2,0],['T1',L2,0],['T2',L5,0],['T3',L2,0]]);
	R3.init_setup([['S1',L2,1],['S2',L2,1],['S3',L6,1],['T1',L3,0],['T2',L2,1],['T3',L3,0]]);
	R4.init_setup([['S1',L3,1],['S2',L3,1],['S3',L3,1],['T1',L7,0],['T2',L3,1],['T3',L8,0]]);
		
	#Start of simulation.
	global time_start
	time_start = time.time()

	t = _thread.start_new_thread(variable_poll,())

	S1.flow_init(0.5,'T1',35*(10e4))	
	S2.flow_init(10,'T2',15*(10e4))	
	S3.flow_init(20,'T3',30*(10e4))	
	time.sleep(190)
	return
	
def test_own():
	H1 = Host('H1',30)
	H2 = Host('H2',30)
	R = Router('R',10)
	L1 = biDirectionalLink(1000000,3,H1,R,32000,'L1',0)   # ASK TA about 32 or 64
	L2 = biDirectionalLink(1000000,3,R,H2,32000,'L2',5)
	H1.link_setup(L1,0)
	H2.link_setup(L2,1)
	RoutingTable = [['H1',L1,1],['H2',L2,0]]
	R.init_setup(RoutingTable)
	
	global time_start
	time_start = time.time()
	H1.flow_init(0.5,'H2',10000)	
	H2.flow_init(0,'H1',5000)
	time.sleep(30)	
	return
		
test0()
