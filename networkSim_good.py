import time
import threading
import _thread
import math
import queue
import random

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
	######################################################################
	##This host class can handle packets from one src/dst only. That is ##
	##okay for our current simulation purposes.                         ##
	######################################################################
	def __init__(self,name,timeout):
		self.pkt_num = 0
		self.name = name
		self.genDelay = 0.000001
		self.timeout = timeout
		##################################################################
		##retransmitPhase: one entry maintained for each destination.   ##
		##				   Is the flow in retransmit phase?             ##
		##window:          one entry maintained per destination.        ##
		##                 The window size for the src-dst pair.        ##
		##lastAck:         one entry per destination.                   ##
		##                 [0]:#pkt for last ack received fron the dst. ##
		##                 [1]:#times ack for the last pkt is received. ##
		##recPktQueue:     one entry per "active" packet.               ##
		##outstandingCnt:  one entry per destination                    ##
		##                 [0]: #unacknowledged packets for the src-dst ##
		##pktList:         one entry for each packet in flight.         ##
		##                 [0]:Time at which pkt was sent.              ##
		##                 [1]:Packet number of the packet.             ##
		##                 [2]:Destination of the packet.               ##
		##                 [3]:Size of the packet.                      ##
		##################################################################
		self.sstart = 0
		self.retransmitPhase = 0
		self.window = 50
		self.maxPktNum = 1000
		self.pktList = list()
		self.recAckQueue = list()
		self.recPktQueue = list()
		self.pktLost = list()
		self.outstandingCnt = 0
		self.pktLossCnt = 0
		self.lastAckTime = 0
		self.recExec = 0
		self.flowSrc = ''
		self.flowDst = ''
		
		self.pktListLock = threading.RLock()
		self.recPktLock = threading.RLock()
		self.recAckLock = threading.RLock()
		self.windowChangeLock = threading.RLock()
		
		_thread.start_new_thread(self.timeout_check,(self.timeout,))
		#_thread.start_new_thread(self.send_rem_ack,())
		_thread.start_new_thread(self.pkt_retransmit,(self.flowDst,))
		return
		
	#add link end specification	
	def link_setup(self,a,b):
		self.outgoing_link = a
		self.outgoing_link_type = b
		return 
	
	#Setup stuff for the flow. Creates a thread for flow_gen and returns immediately.
	def flow_init(self,delay,dst,size):
		self.window = 1
		self.sstart = 1
		t = _thread.start_new_thread(self.flow_gen,(delay,dst,size))
		return 
		
	#Generates the packets of the flow.
	#Packet generation rate to depend on window here.
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
				#print('Append: Pkt list:',[y[1] for y in self.pktList])
				self.outstandingCnt += 1
			finally:
				self.pktListLock.release()
			
			self.pkt_num = self.pkt_num + 1
		print('ALL PACKETS SENT:',self.pkt_num)
		return
		
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
		
	def send_rem_ack(self):
		lastNum = 0
		while 1:
			if time.time()-self.lastAckTime > 10 & len(self.recPktQueue) != 0:
				for f in range(len(self.recPktQueue)):
					if f>0:
						if self.recPktQueue[f] == self.recPktQueue[f-1]+1:
							print('REM_ACK_SEND')
							self.pkt_gen(2,self.flowSrc,1,self.recPktQueue[f],64)
							lastNum = self.recPktQueue[f]
						else:
							print('REM_ACK_SEND')
							self.pkt_gen(2,self.flowSrc,1,lastNum,64)
					else:
						self.pkt_gen(2,self.flowSrc,1,self.recPktQueue[0],64)
				self.lastAckTime = time.time()
			time.sleep(0.001)
		return
		
	#retransmits the dropped packet only. 
	#Waits for acknowledgement for the packet before exiting retransmitPhase.
	#Only one lost packet can be detected at any given time.
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
					self.recAckQueue.append([pktNum,1,3])
					self.recAckQueue.sort()
		
			self.change_window(isPktLoss,src)
			#if self.realLoss == 1 or len(self.pktLost) == 0:
			#	self.change_window(src)
			
			del_idx = [i for i in range(len(self.recAckQueue)) if self.recAckQueue[i][0] < pktNum]
			for j in sorted(del_idx, reverse = True):
				del self.recAckQueue[j]
		
			print('recAckQueue',self.recAckQueue,'Time:',"%0.2f" % (time.time()-time_start))
		
		finally:
			self.recAckLock.release()
		
		return
	
	#Send ack for last packet received w/o pkt loss.	
	def pkt_receive(self,pkt):
		#print('Pkt receive time:',time.time()-time_start)
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
				#print('Ack Gen time:',time.time()-time_start)
				self.pkt_gen(0,pkt.src,1,ackNum,64)
				self.lastAckTime = time.time()
			finally:
				self.recPktLock.release()
			
		else:
			print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
			self.outstandingCnt -= 1
			
			try:
				idx1 = [i for i in range(len(self.pktLost)) if self.pktLost[i][0] <= pkt.pktNum]
				for i in sorted(idx1, reverse=True):
					del self.pktLost[i]
			except ValueError:
				pass
			#print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,)
			self.pktListLock.acquire(1)
			try:	
				try:
					idx = [i for i in range(len(self.pktList)) if self.pktList[i][1] <= pkt.pktNum]
					for i in sorted(idx, reverse=True):
						del self.pktList[i]
				except ValueError:
					pass
			
				self.detect_pkt_loss(pkt.pktNum,pkt.src)
				print('Ack received for packet no:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start),'window:',self.window,'outstandingCnt',self.outstandingCnt)
			
			finally:
				self.pktListLock.release()
		return
	
	#This changes according to the congestion control algorithm.
	#Currently TCP Reno is implemented.
	def change_window(self,pktLoss,src):
		self.windowChangeLock.acquire(1)
		try:
			if pktLoss:
				self.window = math.floor(self.window/2)
				self.sstart = 0
			else:
				#self.window = self.window
				if self.sstart == 1:
					self.window = self.window + 1
				else:
					self.window = self.window + 1/self.window
		finally:
			self.windowChangeLock.release()
		return
		
	#Add timeout mechanism
	def timeout_check(self,timeout):
		while 1:
			for y in self.pktList:
				if time.time()-time_start - y[0] >= timeout:
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
		return



class TCPFast(object):
    
    '''Processes an acknowledgement packet and update window size for FAST TCP'''
    def acknowledgement_received(self, packet):	
        if self.wake_event != None:
            self.event_scheduler.cancel_event(self.wake_event)
        
        # Check if this is a duplicate acknowledgement
        if self.last_ack_received == packet.next_id:
            self.duplicate_count += 1
            keys = [key for key in self.not_acknowledged.keys() if key[0] == packet.next_id]
            # After 3 duplicate acknowledgements, if the packet has not
            # already been received, it has been dropped so it needs to be re-sent
            if (self.duplicate_count == 3) and (len(keys) > 0):
                expected = keys[0]
                del self.not_acknowledged[(packet.next_id, expected[1])]
                self.timed_out.append((packet.next_id, expected[1]))
        else:
            # reset duplicate count since the chain of dupACKS is broken
            self.duplicate_count = 0

        self.last_ack_received = packet.next_id

        # This acknowledgement is for an unacknowledged packet
        if (packet.identifier, packet.duplicate_num) in self.not_acknowledged.keys():
            # calculate RTT of this packet
            rtt = self.clock.current_time - self.not_acknowledged[(packet.identifier, packet.duplicate_num)]
            # first packet, initialize base_RTT
            if self.base_RTT == -1:
                self.base_RTT = rtt
            # update window size
            self.cwnd = self.cwnd * self.base_RTT / rtt + self.alpha
            # update minimum RTT
            if rtt < self.base_RTT:
                self.base_RTT = rtt
            # Remove received packet from list of unacknowledged packets
            del self.not_acknowledged[(packet.identifier, packet.duplicate_num)]

        # Check for any unacknowledged packets that have timed out
        for (packet_id, dup_num) in self.not_acknowledged.keys():
            sent_time = self.not_acknowledged[(packet_id, dup_num)]
            time_diff = self.clock.current_time - sent_time
            if time_diff > self.timeout:
                del self.not_acknowledged[(packet_id, dup_num)]
                self.timed_out.append((packet_id, dup_num))
        if len(self.timed_out) > 0:
            self.retransmit = True
            self.cwnd /= 2
        else:
            self.retransmit = False

        self.send_packet()
        self.wake_event = self.event_scheduler.delay_event(self.timeout, FlowWakeEvent(self.flow))

    '''Sends packets while the number of packets in transit is within the window size'''
    def send_packet(self):
        if self.retransmit == True:
            # send timed out packets. Their duplicate number will be incremented
            while (len(self.not_acknowledged) < self.cwnd) and (len(self.timed_out) > 0):
                (packet_id, dup_num) = self.timed_out[0]
                self.not_acknowledged[(packet_id, dup_num + 1)] = self.clock.current_time
                self.flow.send_a_packet(packet_id, dup_num + 1)
                del self.timed_out[0]
        else:
            # send new packets
            while (len(self.not_acknowledged) < self.cwnd) and (self.window_start * 1024 < self.flow.total):
                self.not_acknowledged[(self.window_start, 0)] = self.clock.current_time
                self.flow.send_a_packet(self.window_start, 0)
                self.window_start += 1

    '''Start sending packets when congestion control first begins or if the flow times out'''
    def wake(self):
        # Check for any unacknowledged packets that have timed out
        for packet_id in self.not_acknowledged.keys():
            sent_time = self.not_acknowledged[packet_id]
            time_diff = self.clock.current_time - sent_time
            if time_diff > self.timeout:
                del self.not_acknowledged[packet_id]
                self.timed_out.append(packet_id)
            if len(self.timed_out) > 0:
                self.retransmit = True
            else:
                self.retransmit = False
                
        self.cwnd /= 2
        self.send_packet() 
        self.wake_event = self.event_scheduler.delay_event(self.timeout, FlowWakeEvent(self.flow))    









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
				#print('Packet inserted:',packet.pktNum,packet.type)
				self.queue.append((packet, destination))
				#print([y[0].pktNum for y in self.queue],[y[1].name for y in self.queue])
				self.available_space -= packet.size
				self.itemsPut += 1
			else:
				print('Packet dropped:',packet.pktNum,packet.type)
				#print('Buf contents:',[pkt.pktNum for (pkt,dst) in self.queue])
				self.drop_pkt += 1
		finally:	
			self.queueLock.release()
		return
		
	#retrieve the next packet from the buffer in order.
	def get(self):
		self.queueLock.acquire()
		try:
			(packet, destination) = self.queue.pop(0)
			#print('Get:',[y[0].pktNum for y in self.queue],[y[1].name for y in self.queue])
			self.available_space += packet.size
			self.itemsPop += 1
			#print('Packet popped',packet.pktNum,destination.name)
		finally:	
			self.queueLock.release()
		
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
					#print(self.name,'Channel switch',"%0.2f" % (time.time()-time_start),)
					self.t1_start = time.time()
					self.channel0Active  = 0
					self.channel1Active  = 1
			else:
				if (time.time() - self.t1_start >= T) or (self.buffer_1.itemsPut - self.buffer_1.itemsPop == 0 and self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0):
					#print(self.name,'Channel switch',"%0.2f" % (time.time()-time_start),)
					self.t0_start = time.time()
					self.channel0Active  = 1
					self.channel1Active  = 0
		return
		
	def propPkt(self,pkt, dst):
		#propagates the pkt through the link with propDelay delay.
		#pkt_receive of both hosts and routers should be constant delay functions.
		time.sleep(self.propDelay)
		#print('Propagation delay completed')
		dst.pkt_receive(pkt)
		#print('Pkt_receive of sender exited')
		return 
		
	def sendPkt(self):
		## pull out packets from the queues depending on whether channel is active or not.
		## sleep for transDelay.
		## spawn process for propPkt
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
		#print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start))
		self.buffer_0.put(pkt,self.dst_dir0)
		print('Channel 0 active:',self.channel0Active)
		return
		
	def onreceive_dir1(self,pkt):
		#print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start))
		self.buffer_1.put(pkt,self.dst_dir1)
		return

class biDirectionalLinkv2(object):
	#figure out something for queue ends. Behaviour depends on which queue end packet came from.
	def __init__(self,a,b,src,dst,size,name):
		self.rate = a
		self.propDelay = b
		self.src_dir0 = src
		self.dst_dir0 = dst
		self.src_dir1 = dst
		self.dst_dir1 = src
		self.name = name
		self.buffer = Buffer(size, self.name+'Buf')
		#_thread.start_new_thread(self.activeChannel,(self.start_delay,))
		_thread.start_new_thread(self.sendPkt,())
		return
		
	def propPkt(self,pkt, dst):
		#propagates the pkt through the link with propDelay delay.
		#pkt_receive of both hosts and routers should be constant delay functions.
		time.sleep(self.propDelay)
		#print('End propagation')
		dst.pkt_receive(pkt)
		return 
		
	def sendPkt(self):
		while 1:
			if len(self.buffer.queue)!=0:
				(pkt, dst) = self.buffer.get()
				transmission_delay = pkt.size / self.rate
				time.sleep(transmission_delay)
				#print('Start propagation')
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
	while 1:
		#print('H1.window:',H1.window)
		#print('H1.retransmit_phase',H1.retransmitPhase,'H1.sstart',H1.sstart,'H1.outstandingCnt',H1.outstandingCnt,'H1.window',H1.window,'Time:',"%0.2f" % (time.time()-time_start))
		#print('H1.pktList',[y[1] for y in H1.pktList])
		#print('H2.recPktQueue',H2.recPktQueue)
		#print('H1.recAckQueue',H1.recAckQueue)
		#print('L1 Buf',[y[0].pktNum for y in L1.buffer.queue],[y[1].name for y in L1.buffer.queue])
		time.sleep(0.01)
	return
	
def test0():
	#Host initialization.
	global RTT
	RTT = 0.04
	global H1
	H1 = Host('H1',200*RTT)
	global H2
	H2 = Host('H2',200*RTT)
		
	#Link Initialization.
	global L1
	#L1 = biDirectionalLink((10e6)/8,0.01,H1,H2,32*(10e2),'L1',0)
	L1 = biDirectionalLinkv2((10e6)/8,0.01,H1,H2,64*(10e2),'L1')
		
	#Link setup for hosts.
	H1.link_setup(L1,0)
	H2.link_setup(L1,1)
		
	#Start of simulation.
	global time_start
	time_start = time.time()

	t = _thread.start_new_thread(variable_poll,())
	
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
		
test0()
