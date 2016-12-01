def test0():
	#Host initialization.
	global RTT
	RTT = 0.02
	global H1
	H1 = Host('H1',100*RTT,'FAST')
	global H2
	H2 = Host('H2',100*RTT,'FAST')
		
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
	
	#List setup for variable_poll.
	hostList.append(H1)
	linkList.append(L1)
	
	#Start of simulation.
	global time_start
	time_start = time.time()

	t = _thread.start_new_thread(variable_poll,())
	
	H1.flow_init(1.0,'H2',20*(10e5))	
	time.sleep(700)
	return
	