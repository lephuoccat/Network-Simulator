import time
import _thread
import queue

#eventQueue = queue.Queue()	#do we need this??

#add router class
#check thoroughly for thread execution locks

#Talk to TA whether this "virtual" packet is fine or not.
class Packet:
	def __init__(self,src,dst,type,pktNum):
		self.src = src
		self.dst = dst
		self.type = type
		self.pktNum = pktNum
		
class Host(object):
	def __init__(self,name):
		self.pkt_num = 0
		self.name = name
		
	#add link end specification	
	def link_setup(self,a,b):
		self.incoming_link = a
		self.outgoing_link = b
		return 
	
	#improve packet generation. Add code for sending packets one after the other. Needed for flooding network.
	def pkt_gen(self,delay,dst,type,pktNum):
		time.sleep(delay)
		pkt = Packet(self,dst,type,pktNum)
		self.pkt_num = self.pkt_num+1
		print('Packet number sent by host:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		t = _thread.start_new_thread(self.outgoing_link.onreceive,(pkt,))
		return 
		
	#def pkt_sent(self,pkt):
	#	print('Packet number sent by host:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
	#	self.outgoing_link.onreceive(pkt)
	#	return
		
	#def ack_gen(self,pkt):
	#	self.pkt_gen(0,64,pkt.dst,pkt.pktNum)
	#	return
		
	#def pkt_loss(self):
	#	self.ch_window(1)
	#	return
		
	def pkt_receive(self,pkt):
	#add window change logic
		print('Packet no. received by Host:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		if pkt.type == 0:
			print('Ack for packet number:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
			t = _thread.start_new_thread(self.pkt_gen,(2,pkt.src,1,pkt.pktNum))
		return
	
	#detect packet loss somehow.
	
	#def ch_window(self,isLoss):
	#	if isLoss:
	#		window = window/2
	#		else
	#		window = window + 1
	#	return
		
	#Add timeout mechanism
	#def timeout(self):
	#	window = 1
	#	return


class Link(object):
	#figure out something for queue ends. Behaviour depends on which queue end packet came from.
	def __init__(self,a,b,src,dst,size,name):
		self.transDelay = a
		self.propDelay = b
		self.src = src
		self.dst = dst
		self.name = name
		#need to initialize queues (two of them) here.
		self.bufSize = size
	
	#two instances of this for the two directions. 	
	def onreceive(self,pkt):
		print('Packet no. received by link:',self.name,pkt.pktNum,'Time:',(int)(time.time()-time_start))
		#need to queue here. Check for 
		#spawn separate process for packet drop here.
		time.sleep(self.transDelay+self.propDelay)
		t = _thread.start_new_thread(self.dst.pkt_receive,(pkt,))
		#self.dst.pkt_receive(pkt)
		return
		
A = Host('A')
B = Host('B')
C = Link(1,3,A,B,64,'C')
D = Link(1,2,B,A,64,'D')
A.link_setup(D,C)
B.link_setup(C,D)

time_start = time.time()	
A.pkt_gen(3,B,0,A.pkt_num)
A.pkt_gen(0,B,0,A.pkt_num)
A.pkt_gen(0,B,0,A.pkt_num)
#figure out better way to do this. Check for end of all threads
time.sleep(10)	




