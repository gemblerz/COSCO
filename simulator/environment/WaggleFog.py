import numpy as np
import logging as logger
from simulator.host.Host import *
from simulator.host.Disk import *
from simulator.host.RAM import *
from simulator.host.Bandwidth import *
from metrics.powermodels.PMJetsonXavierNX import *
from metrics.powermodels.PMRaspberryPi import *

class WaggleFog():
	def __init__(self, hosts):
		self.hosts = hosts
		self.num_hosts = len(hosts)
		self.types = {
			'wildnode': {
				"IPS": 100000,
				"RAMSize": 8000,
				"RAMRead": 59000,
				"RAMWrite": 59000,
				"DiskSize": 512000,
				"DiskRead": 3500,
				"DiskWrite": 2500,
				"BwUp": 10,
				"BwDown": 1,
			}
 		}

	def generateHosts(self):
		hosts = []
		groups = []
		for host in self.hosts:
			logger.debug(f'generating a host for {host}')
			typeID = host["type"]
			IPS = self.types[typeID]['IPS']
			Ram = RAM(self.types[typeID]['RAMSize'], self.types[typeID]['RAMRead']*5, self.types[typeID]['RAMWrite']*5)
			Disk_ = Disk(self.types[typeID]['DiskSize'], self.types[typeID]['DiskRead']*5, self.types[typeID]['DiskWrite']*10)
			Bw = Bandwidth(self.types[typeID]['BwUp'], self.types[typeID]['BwDown'])
			Power = PMJetsonXavierNX()
			groupName = host["group"]
			if groupName in groups:
				groupID = groups.index(groupName)
			else:
				groups.append(groupName)
				groupID = groups.index(groupName)

			# Latency = 0.003 if i < self.edge_hosts else 0.076
			hosts.append(Host(IPS, Ram, Disk_, Bw, 0, Power, groupID))
		return hosts