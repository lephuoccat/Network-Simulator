import time
import threading
import _thread
import math
import queue
import random
#import matplotlib.pyplot as plt

global pktSize 
pktSize = 1000

global hostList
hostList = list()
global linkList 
linkList = list()

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