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
			print('#','i',i,'Time',time.time()-time_start,'Control passed over to flow_gen')
			self.pkt_gen(0,dst,0,self.pkt_num,pktSize)
			self.pkt_num = self.pkt_num + 1
			
			self.pktListLock.acquire(1)
			try:
				self.pktList.append([time.time()-time_start,self.pkt_num,dst,pktSize])
				print('#','Append: Pkt list:',[y[1] for y in self.pktList])
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
		print('#','ALL PACKETS SENT:',self.pkt_num)
		return
		
	#Generates packet with size=pktSize & packet number=pktNum. Sends generated packet to 
	#the outgoing link.
	def pkt_gen(self,delay,dst,type,pktNum,pktSize):
		time.sleep(delay)
		pkt = Packet(self.name,dst,type,pktNum,pktSize)
		
		if pkt.type == 0:
			print('#','Packet number sent by host:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
		
		else:
			print('#','Ack sent for packet number:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
		
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
				print('#','Pkt lost list:',self.pktLost)
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
						print('#','RETRANSMIT PHASE STARTED')
						while self.outstandingCnt >= self.window:
							time.sleep(0.0001)
						try:
							k = [y[1] for y in self.pktList].index(currPkt)
							self.pkt_gen(0,self.flowDst,0,self.pktList[k][1],self.pktList[k][3])
							self.pktList[k][0] = time.time()-time_start
							self.outstandingCnt += 1
							print('#','Packet retransmitted:',self.pktList[k][1])
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
								print('#','RETRANSMIT PHASE ENDED')
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
					print('#','PKT LOSS DETECTED','Time:',"%0.2f" % (time.time()-time_start))
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
		
			print('#','recAckQueue',self.recAckQueue,'Time:',"%0.2f" % (time.time()-time_start))
		
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
				
				print('#','Packet number received by host:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
			
				try:
					idx = self.recPktQueue.index(pkt.pktNum)
				except ValueError:
					if pkt.pktNum > self.lastAckSent:
						self.recPktQueue.append(pkt.pktNum)
				if len(self.recPktQueue) != 0:
					self.recPktQueue.sort()	
			
				print('#','recPktQueue:',self.recPktQueue)
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
			print('#','Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
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
				print('#','Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,'outstandingCnt',self.outstandingCnt)
			
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
					self.window = math.ceil(self.window/2)
					self.sstart = 0
				else:
					if self.sstart == 1:
						self.window = self.window + 1
					else:
						if self.window != 0:
							self.window = self.window + 1/self.window
						else:
							self.window = 1
			else:
				if pktLoss:
					self.sstart = 0
				if self.curr_RTT != 0:
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
						print('#','Timeout occured')
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
						print('#','Timeout: Pkt retransmitted:',y[1],'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window)
						break
			time.sleep(0.001)
		return