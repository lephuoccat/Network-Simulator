def variable_poll():
	dropStatList = list()
	for item in linkList:
		dropStatList.append([0,item])
		
	while 1:
		print("%0.2f" % (time.time()-time_start)+' ,',end = ' ')
		for item in hostList:
			print(repr(item.window)+' ,',end = ' ')
			
		for item1 in hostList:
			print(repr(item1.curr_RTT-item1.base_RTT)+' ,',end = ' ')
		
		for item2 in linkList:
			m = [y[1] for y in dropStatList].index(item2)
			print(repr(item2.buffer.drop_pkt-dropStatList[m][0])+' ,',end = ' ')
			if dropStatList[m][0] != item2.buffer.drop_pkt:
				dropStatList[m][0] = item2.buffer.drop_pkt
		
		for item3 in linkList:
			if item3 != linkList[-1]:
				print(repr(1-item3.buffer.available_space/(64000))+' ,',end = ' ')
			else:
				print(repr(1-item3.buffer.available_space/(64000)))
		time.sleep(0.01)
	
	# while 1:
		# for link in Logger.bufferOccupancy :
			# Logger.bufferOccupancy[link].append(link.buffer.size-link.buffer.available_space)
		# for host in Logger.windowSize :
			# Logger.windowSize[host].append(host.window)
		# for host in Logger.delays :
			# Logger.delays[host].append(host.genDelay)
		#print('H1.window:',H1.window)
		#print('H1.retransmit_phase',H1.retransmitPhase,'H1.sstart',H1.sstart,'H1.outstandingCnt',H1.outstandingCnt,'H1.window',H1.window,'Time:',"%0.2f" % (time.time()-time_start))
		#print('H1.pktList',[y[1] for y in H1.pktList])
		#print('H2.recPktQueue',H2.recPktQueue)
		#print('H1.recAckQueue',H1.recAckQueue)
		#print('L1 Buf',[y[0].pktNum for y in L1.buffer.queue],[y[1].name for y in L1.buffer.queue])
		#time.sleep(0.01)
	return