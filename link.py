class Buffer:
	def __init__(self, size, link):
        self.available_space = size
        self.link = link
        self.queue = Queue.Queue()
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger
        self.logger.log_link_buffer_available_space(self.link.identifier, self.available_space)

    # Places a packet in the buffer, or drops the packet if no space is available
    def put(self, packet, destination):
        if self.available_space >= packet.size:
            self.queue.put((packet, destination))
            self.available_space -= packet.size
            self.logger.log_link_buffer_available_space(self.link.identifier, self.available_space)
        # Otherwise, drop the packet
        else:
            self.logger.log_link_dropped_packet_buffer_full(self.link.identifier, packet)

	#Retrieves the next packet from the buffer in order
    def get(self):
        (packet, destination) = self.queue.get_nowait()
        self.available_space += packet.size
        self.logger.log_link_buffer_available_space(self.link.identifier, self.available_space)
        return (packet, destination)



class Link:

	def __init__(self, identifier, rate, delay, buffer_size, deviceA, deviceB):
        self.identifier = identifier
        self.rate = rate
        self.delay = delay
        self.buffer = Buffer(buffer_size, self)
        self.deviceA = deviceA
        self.deviceB = deviceB
        self.busy = False
        
    # Sends a packet instantly if the link is not busy
    # or enqueues the packet in the buffer if the link is busy
    def send_packet(self, packet, sender):

        # The recipient is whatever device is not the sender
        recipient = self.other_device(sender)
        # Place in buffer if busy, otherwise send now
        if not self.busy:
            self._send_packet_now(packet, recipient)
            self.logger.log_link_sent_packet_immediately(self.identifier, packet)
        else:
            self.buffer.put(packet, recipient)

    # Called internally to send a packet by scheduling the relevant events
    def _send_packet_now(self, packet, recipient):
        assert not self.busy
        self.busy = True

        sending_delay = packet.size / self.rate
        self.event_scheduler.delay_event(sending_delay + self.delay, PacketArrivalEvent(packet, recipient, self))
        self.event_scheduler.delay_event(sending_delay, LinkReadyEvent(self))

    # Send a packet from the buffer, if possible
    def wake(self):
        self.busy = False
        try:
            # If there are any packets in the buffer, send one
            (packet, destination) = self.buffer.get()
            self._send_packet_now(packet, destination)
            self.logger.log_link_sent_packet_from_buffer(self.identifier, packet)
        except Queue.Empty:
            pass