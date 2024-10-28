from simulator.host.Disk import *
from simulator.host.RAM import *
from simulator.host.Bandwidth import *

class Host():
	# IPS = Million Instructions per second capacity 
	# RAM = Ram in MB capacity
	# Disk = Disk characteristics capacity
	# Bw = Bandwidth characteristics capacity
	def __init__(self, IPS, RAM, Disk, Bw, Latency, Powermodel, groupID=0):
		self.id = -1
		self.env = None
		self.ipsCap = IPS
		self.ramCap = RAM
		self.diskCap = Disk
		self.bwCap = Bw
		self.latency = Latency
		self.powermodel = Powermodel
		self.powermodel.allocHost(self)
		self.powermodel.host = self
		self.group = groupID

	def associate(self, myID, env):
		self.id = myID
		self.env = env

	def getPower(self):
		return self.powermodel.power()

	def getPowerFromIPS(self, ips):
		return self.powermodel.powerFromCPU(min(100, 100 * (ips / self.ipsCap)))
		
	def getCPU(self):
		ips = self.getApparentIPS()
		return 100 * (ips / self.ipsCap)

	def getBaseIPS(self):
		# Get base ips count as sum of min ips of all containers
		ips = 0
		containers = self.env.getContainersOfHost(self.id)
		for containerID in containers:
			ips += self.env.getContainerByID(containerID).getBaseIPS()
		# assert ips <= self.ipsCap
		return ips

	def getApparentIPS(self):
		# Give containers remaining IPS for faster execution
		ips = 0
		containers = self.env.getContainersOfHost(self.id)
		for containerID in containers:
			ips += self.env.getContainerByID(containerID).getApparentIPS()
		# assert int(ips) <= self.ipsCap
		return int(ips)

	def getIPSAvailable(self):
		# IPS available is ipsCap - baseIPS
		# When containers allocated, existing ips can be allocated to
		# the containers
		return self.ipsCap - self.getBaseIPS()

	def getCurrentRAM(self):
		size, read, write = 0, 0, 0
		containers = self.env.getContainersOfHost(self.id)
		for containerID in containers:
			s, r, w = self.env.getContainerByID(containerID).getRAM()
			size += s; read += r; write += w
		# assert size <= self.ramCap.size
		# assert read <= self.ramCap.read
		# assert write <= self.ramCap.write
		return size, read, write

	def getRAMAvailable(self):
		size, read, write = self.getCurrentRAM()
		return self.ramCap.size - size, self.ramCap.read - read, self.ramCap.write - write

	def getCurrentDisk(self):
		size, read, write = 0, 0, 0
		containers = self.env.getContainersOfHost(self.id)
		for containerID in containers:
			s, r, w = self.env.getContainerByID(containerID).getDisk()
			size += s; read += r; write += w
		assert size <= self.diskCap.size
		assert read <= self.diskCap.read
		assert write <= self.diskCap.write
		return size, read, write

	def getDiskAvailable(self):
		size, read, write = self.getCurrentDisk()
		return self.diskCap.size - size, self.diskCap.read - read, self.diskCap.write - write
