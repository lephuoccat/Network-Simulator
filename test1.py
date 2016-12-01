def test1():
	global RTT
	RTT = 0.06
	
	#Host initialization.
	global H1
	H1 = Host('H1',RTT*200,'RENO')			
	global H2
	H2 = Host('H2',RTT*200,'RENO')
		
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
		
	hostList.append(H1)
	linkList.append(L0)
	linkList.append(L1)
	linkList.append(L2)
	linkList.append(L3)
	linkList.append(L4)
	linkList.append(L5)
	
	global alpha
	alpha = 15
	global gamma
	gamma = 0.5
	#Start of simulation.
	global time_start
	time_start = time.time()

	#t = _thread.start_new_thread(variable_poll,())

	H1.flow_init(0.5,'H2',20*(10e5))	
	time.sleep(800)
	return