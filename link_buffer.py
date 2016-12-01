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
				print('#','Packet dropped:',packet.pktNum,packet.type)
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
				print('#','#',self.name,':Channel 0 active',"%0.2f" % (time.time()-time_start))
				if self.buffer_0.itemsPut - self.buffer_0.itemsPop != 0:
					(pkt, dst) = self.buffer_0.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					_thread.start_new_thread(self.propPkt,(pkt,dst))
				else:
					time.sleep(0.00001)
			if self.channel1Active == 1:
				print('#',self.name,':Channel 1 active',"%0.2f" % (time.time()-time_start))
				if self.buffer_1.itemsPut - self.buffer_1.itemsPop != 0:
					(pkt, dst) = self.buffer_1.get()
					transmission_delay = pkt.size / self.rate
					time.sleep(transmission_delay)
					print('#','Before thread start')
					_thread.start_new_thread(self.propPkt,(pkt,dst))
					print('#','thread started')
				else:
					time.sleep(0.00001)
		return
		
	def onreceive_dir0(self,pkt):
		self.buffer_0.put(pkt,self.dst_dir0)
		print('#','Channel 0 active:',self.channel0Active)
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
		print('#','Packet no. received by link:',self.name,pkt.pktNum,'Time:',"%0.2f" % (time.time()-time_start))
		time.sleep(self.transDelay+self.propDelay)
		t = _thread.start_new_thread(self.dst.pkt_receive,(pkt,))
		return