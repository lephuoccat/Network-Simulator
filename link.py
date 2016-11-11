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

class Link:

	def __init__(self, identifier, rate, delay, buffer_size, deviceA, deviceB):
        self.identifier = identifier
        self.rate = rate
        self.delay = delay
        self.buffer = Buffer(buffer_size, self)
        self.deviceA = deviceA
        self.deviceB = deviceB
        