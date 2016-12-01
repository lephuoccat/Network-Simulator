def test2():
	global RTT
	RTT = 0.06
	
	#Host initialization.
	global S1
	S1 = Host('S1',RTT*150,'RENO')	
	global S2
	S2 = Host('S2',RTT*150,'RENO')
	global S3
	S3 = Host('S3',RTT*150,'RENO')	
	global T1
	T1 = Host('T1',RTT*150,'RENO')	
	global T2
	T2 = Host('T2',RTT*150,'RENO')	
	global T3
	T3 = Host('T3',RTT*150,'RENO')		
		
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
	
	global alpha
	alpha = 15
	global gamma
	gamma = 0.5
	
	#Start of simulation.
	global time_start
	time_start = time.time()

	#t = _thread.start_new_thread(variable_poll,())

	S1.flow_init(0.5,'T1',35*(10e4))	
	S2.flow_init(10,'T2',15*(10e4))	
	S3.flow_init(20,'T3',30*(10e4))	
	time.sleep(250)
	return