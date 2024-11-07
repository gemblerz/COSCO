import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from scheduler.GOBI import GOBIScheduler
from torch.utils.tensorboard import SummaryWriter
# from tensorboardX import SummaryWriter

plt.style.use(['science'])
plt.rcParams["text.usetex"] = False

class Stats():
	def __init__(self, Environment, WorkloadModel, Datacenter, Scheduler, viz=None):
		self.env = Environment
		self.env.stats = self
		self.workload = WorkloadModel
		self.datacenter = Datacenter
		self.scheduler = Scheduler
		# We disabled the GOBI scheduler in the Stats class as it does only predictions
		# which we do not want, at least for now.
		# self.simulated_scheduler = GOBIScheduler('energy_latency_'+str(self.datacenter.num_hosts))
		# self.simulated_scheduler.env = self.env
		self.initStats()
		self.viz = SummaryWriter(log_dir=f'./tb/{Scheduler.__module__}/')

	def initStats(self):	
		self.hostinfo = []
		self.workloadinfo = []
		self.activecontainerinfo = []
		self.allcontainerinfo = []
		self.metrics = []
		self.schedulerinfo = []

	def saveHostInfo(self):
		hostinfo = dict()
		hostinfo['interval'] = self.env.interval
		hostinfo['cpu'] = [host.getCPU() for host in self.env.hostlist]
		hostinfo['numcontainers'] = [len(self.env.getContainersOfHost(i)) for i,host in enumerate(self.env.hostlist)]
		hostinfo['power'] = [host.getPower() for host in self.env.hostlist]
		hostinfo['baseips'] = [host.getBaseIPS() for host in self.env.hostlist]
		hostinfo['ipsavailable'] = [host.getIPSAvailable() for host in self.env.hostlist]
		hostinfo['ipscap'] = [host.ipsCap for host in self.env.hostlist]
		hostinfo['apparentips'] = [host.getApparentIPS() for host in self.env.hostlist]
		hostinfo['ram'] = [host.getCurrentRAM() for host in self.env.hostlist]
		hostinfo['ramavailable'] = [host.getRAMAvailable() for host in self.env.hostlist]
		hostinfo['disk'] = [host.getCurrentDisk() for host in self.env.hostlist]
		hostinfo['diskavailable'] = [host.getDiskAvailable() for host in self.env.hostlist]
		self.hostinfo.append(hostinfo)

		# Publish to viz
		for i, host in enumerate(self.env.hostlist):
			self.viz.add_scalar(f'Host/cpu/{i}', host.getCPU(), self.env.interval)
			self.viz.add_scalar(f'Host/numcontainers/{i}', len(self.env.getContainersOfHost(i)), self.env.interval)
			self.viz.add_scalar(f'Host/power/{i}', host.getPower(), self.env.interval)
			self.viz.add_scalar(f'Host/baseips/{i}', host.getBaseIPS(), self.env.interval)
			self.viz.add_scalar(f'Host/ipsavailable/{i}', host.getIPSAvailable(), self.env.interval)
			self.viz.add_scalar(f'Host/ipscap/{i}', host.ipsCap, self.env.interval)
			self.viz.add_scalar(f'Host/apparentips/{i}', host.getApparentIPS(), self.env.interval)
			# getCurrentRAM returns (size, read, write) and we take the size only
			self.viz.add_scalar(f'Host/ram/{i}', host.getCurrentRAM()[0], self.env.interval)
			# getRAMAvailable returns (size, read, write) and we take the size only
			self.viz.add_scalar(f'Host/ramavailable/{i}', host.getRAMAvailable()[0], self.env.interval)
			# getCurrentDisk returns (size, read, write) and we take the size only
			self.viz.add_scalar(f'Host/disk/{i}', host.getCurrentDisk()[0], self.env.interval)
			# getDiskAvailable returns (size, read, write) and we take the size only
			self.viz.add_scalar(f'Host/diskavailable/{i}', host.getDiskAvailable()[0], self.env.interval)

	def saveWorkloadInfo(self, deployed, migrations):
		workloadinfo = dict()
		workloadinfo['interval'] = self.env.interval
		workloadinfo['totalcontainers'] = len(self.workload.createdContainers)
		if self.workloadinfo != []:
			workloadinfo['newcontainers'] = workloadinfo['totalcontainers'] - self.workloadinfo[-1]['totalcontainers'] 
		else:
			workloadinfo['newcontainers'] = workloadinfo['totalcontainers']
		workloadinfo['deployed'] = len(deployed)
		workloadinfo['migrations'] = len(migrations)
		workloadinfo['inqueue'] = len(self.workload.getUndeployedContainers())
		self.workloadinfo.append(workloadinfo)

		self.viz.add_scalar(f'Containers/total', len(self.workload.createdContainers), self.env.interval)
		self.viz.add_scalar(f'Containers/new', workloadinfo['newcontainers'], self.env.interval)
		self.viz.add_scalar(f'Containers/deployed', len(deployed), self.env.interval)
		self.viz.add_scalar(f'Containers/migrations', len(migrations), self.env.interval)
		self.viz.add_scalar(f'Containers/inqueue', len(self.workload.getUndeployedContainers()), self.env.interval)

	def saveContainerInfo(self):
		containerinfo = dict()
		containerinfo['interval'] = self.env.interval
		containerinfo['activecontainers'] = self.env.getNumActiveContainers()
		containerinfo['ips'] = [(c.getBaseIPS() if c else 0) for c in self.env.containerlist]
		containerinfo['apparentips'] = [(c.getApparentIPS() if c else 0) for c in self.env.containerlist]
		containerinfo['ram'] = [(c.getRAM() if c else 0) for c in self.env.containerlist]
		containerinfo['disk'] = [(c.getDisk() if c else 0) for c in self.env.containerlist]
		containerinfo['creationids'] = [(c.creationID if c else -1) for c in self.env.containerlist]
		containerinfo['hostalloc'] = [(c.getHostID() if c else -1) for c in self.env.containerlist]
		containerinfo['active'] = [(c.active if c else False) for c in self.env.containerlist]
		self.activecontainerinfo.append(containerinfo)

	def saveAllContainerInfo(self):
		containerinfo = dict()
		allCreatedContainers = [self.env.getContainerByCID(cid) for cid in list(np.where(self.workload.deployedContainers)[0])]
		containerinfo['interval'] = self.env.interval
		if self.datacenter.__class__.__name__ == 'Datacenter':
			containerinfo['application'] = [self.env.getContainerByCID(cid).application for cid in list(np.where(self.workload.deployedContainers)[0])]
		containerinfo['ips'] = [(c.getBaseIPS() if c.active else 0) for c in allCreatedContainers]
		containerinfo['create'] = [(c.createAt) for c in allCreatedContainers]
		containerinfo['start'] = [(c.startAt) for c in allCreatedContainers]
		containerinfo['destroy'] = [(c.destroyAt) for c in allCreatedContainers]
		containerinfo['apparentips'] = [(c.getApparentIPS() if c.active else 0) for c in allCreatedContainers]
		containerinfo['ram'] = [(c.getRAM() if c.active else 0) for c in allCreatedContainers]
		containerinfo['disk'] = [(c.getDisk() if c.active else 0) for c in allCreatedContainers]
		containerinfo['hostalloc'] = [(c.getHostID() if c.active else -1) for c in allCreatedContainers]
		containerinfo['active'] = [(c.active) for c in allCreatedContainers]
		self.allcontainerinfo.append(containerinfo)

	def saveMetrics(self, destroyed, migrations):
		metrics = dict()
		metrics['interval'] = self.env.interval
		metrics['numdestroyed'] = len(destroyed)
		metrics['nummigrations'] = len(migrations)
		metrics['energy'] = [host.getPower()*self.env.intervaltime for host in self.env.hostlist]
		metrics['energytotalinterval'] = np.sum(metrics['energy'])
		metrics['energypercontainerinterval'] = np.sum(metrics['energy'])/self.env.getNumActiveContainers()
		metrics['responsetime'] = [c.totalExecTime + c.totalMigrationTime for c in destroyed]
		metrics['avgresponsetime'] = np.average(metrics['responsetime']) if len(destroyed) > 0 else 0
		metrics['migrationtime'] = [c.totalMigrationTime for c in destroyed]
		metrics['avgmigrationtime'] = np.average(metrics['migrationtime']) if len(destroyed) > 0 else 0
		metrics['slaviolations'] = len(np.where([c.destroyAt > c.sla for c in destroyed])[0])
		metrics['slaviolationspercentage'] = metrics['slaviolations'] * 100.0 / len(destroyed) if len(destroyed) > 0 else 0
		metrics['waittime'] = [c.startAt - c.createAt for c in destroyed]
		# metrics['energytotalinterval_pred'], metrics['avgresponsetime_pred'] = self.runSimulationGOBI()
		self.metrics.append(metrics)

		self.viz.add_scalar(f'Stats/numdestroyed', len(destroyed), self.env.interval)
		self.viz.add_scalar(f'Stats/nummigrations', len(migrations), self.env.interval)
		# TODO: What is self.env.intervaltime
		# self.viz.add_scalar(f'Stats/energy', ???, self.env.interval)
		self.viz.add_scalar(f'Stats/energytotalinterval', np.sum(metrics['energy']), self.env.interval)
		self.viz.add_scalar(f'Stats/avgresponsetime', metrics['avgresponsetime'], self.env.interval)
		self.viz.add_scalar(f'Stats/avgmigrationtime', metrics['avgmigrationtime'], self.env.interval)
		self.viz.add_scalar(f'Stats/slaviolations', metrics['slaviolations'], self.env.interval)
		self.viz.add_scalar(f'Stats/slaviolationspercentage', metrics['slaviolationspercentage'], self.env.interval)

	def saveSchedulerInfo(self, selectedcontainers, decision, schedulingtime):
		schedulerinfo = dict()
		schedulerinfo['interval'] = self.env.interval
		schedulerinfo['selection'] = selectedcontainers
		schedulerinfo['decision'] = decision
		schedulerinfo['schedule'] = [(c.id, c.getHostID()) if c else (None, None) for c in self.env.containerlist]
		schedulerinfo['schedulingtime'] = schedulingtime
		if self.datacenter.__class__.__name__ == 'Datacenter':
			schedulerinfo['migrationTime'] = self.env.intervalAllocTimings[-1]
		self.schedulerinfo.append(schedulerinfo)

	def saveStats(self, deployed, migrations, destroyed, selectedcontainers, decision, schedulingtime):	
		self.saveHostInfo()
		self.saveWorkloadInfo(deployed, migrations)
		self.saveContainerInfo()
		self.saveAllContainerInfo()
		self.saveMetrics(destroyed, migrations)
		self.saveSchedulerInfo(selectedcontainers, decision, schedulingtime)

		## NOTE: I want to add my own metrics here
		# self.viz.add_scalar("mymetric", 0, self.env.interval)

	def runSimpleSimulation(self, decision):
		host_alloc = []; container_alloc = [-1] * len(self.env.hostlist)
		for i in range(len(self.env.hostlist)):
			host_alloc.append([])
		for c in self.env.containerlist:
			if c and c.getHostID() != -1: 
				host_alloc[c.getHostID()].append(c.id) 
				container_alloc[c.id] = c.getHostID()
		decision = self.simulated_scheduler.filter_placement(decision)
		for cid, hid in decision:
			if self.env.getPlacementPossible(cid, hid) and container_alloc[cid] != -1:
				host_alloc[container_alloc[cid]].remove(cid)
				host_alloc[hid].append(cid)
		energytotalinterval_pred = 0
		for hid, cids in enumerate(host_alloc):
			ips = 0
			for cid in cids: ips += self.env.containerlist[cid].getApparentIPS()
			energytotalinterval_pred += self.env.hostlist[hid].getPowerFromIPS(ips)
		return energytotalinterval_pred*self.env.intervaltime, max(0, np.mean([metric_d['avgresponsetime'] for metric_d in self.metrics[-5:]]))

	def runSimulationGOBI(self):
		host_alloc = []; container_alloc = [-1] * len(self.env.hostlist)
		for i in range(len(self.env.hostlist)):
			host_alloc.append([])
		for c in self.env.containerlist:
			if c and c.getHostID() != -1: 
				host_alloc[c.getHostID()].append(c.id) 
				container_alloc[c.id] = c.getHostID()
		selected = self.simulated_scheduler.selection()
		decision = self.simulated_scheduler.filter_placement(self.simulated_scheduler.placement(selected))
		for cid, hid in decision:
			if self.env.getPlacementPossible(cid, hid) and container_alloc[cid] != -1:
				host_alloc[container_alloc[cid]].remove(cid)
				host_alloc[hid].append(cid)
		energytotalinterval_pred = 0
		for hid, cids in enumerate(host_alloc):
			ips = 0
			for cid in cids: ips += self.env.containerlist[cid].getApparentIPS()
			energytotalinterval_pred += self.env.hostlist[hid].getPowerFromIPS(ips)
		return energytotalinterval_pred*self.env.intervaltime, max(0, np.mean([metric_d['avgresponsetime'] for metric_d in self.metrics[-5:]]))

	########################################################################################################

	def generateGraphsWithInterval(self, dirname, listinfo, obj, metric, metric2=None):
		fig, axes = plt.subplots(len(listinfo[0][metric]), 1, sharex=True,figsize=(4, 0.5*len(listinfo[0][metric])))
		title = obj + '_' + metric + '_with_interval' 
		totalIntervals = len(listinfo)
		x = list(range(totalIntervals))
		metric_with_interval = []; metric2_with_interval = []
		ylimit = 0; ylimit2 = 0
		for hostID in range(len(listinfo[0][metric])):
			metric_with_interval.append([listinfo[interval][metric][hostID] for interval in range(totalIntervals)])
			ylimit = max(ylimit, max(metric_with_interval[-1]))
			if metric2:
				metric2_with_interval.append([listinfo[interval][metric2][hostID] for interval in range(totalIntervals)])
				ylimit2 = max(ylimit2, max(metric2_with_interval[-1]))
		for hostID in range(len(listinfo[0][metric])):
			axes[hostID].set_ylim(0, max(ylimit, ylimit2))
			axes[hostID].plot(x, metric_with_interval[hostID])
			if metric2:
				axes[hostID].plot(x, metric2_with_interval[hostID])
			axes[hostID].set_ylabel(obj[0].capitalize()+" "+str(hostID))
			axes[hostID].grid(b=True, which='both', color='#eeeeee', linestyle='-')
		plt.tight_layout(pad=0)
		plt.savefig(dirname + '/' + title + '.pdf')

	def generateMetricsWithInterval(self, dirname):
		fig, axes = plt.subplots(9, 1, sharex=True, figsize=(4, 5))
		x = list(range(len(self.metrics)))
		res = {}
		for i,metric in enumerate(['numdestroyed', 'nummigrations', 'energytotalinterval', 'avgresponsetime',\
			 'avgmigrationtime', 'slaviolations', 'slaviolationspercentage', 'waittime', 'energypercontainerinterval']):
			metric_with_interval = [self.metrics[i][metric] for i in range(len(self.metrics))] if metric != 'waittime' else \
				[sum(self.metrics[i][metric]) for i in range(len(self.metrics))]
			axes[i].plot(x, metric_with_interval)
			axes[i].set_ylabel(metric, fontsize=5)
			axes[i].grid(b=True, which='both', color='#eeeeee', linestyle='-')
			res[metric] = sum(metric_with_interval)
			print("Summation ", metric, " = ", res[metric])
		print('Average energy (sum energy interval / sum numdestroyed) = ', res['energytotalinterval']/res['numdestroyed'])
		plt.tight_layout(pad=0)
		plt.savefig(dirname + '/' + 'Metrics' + '.pdf')

	def generateWorkloadWithInterval(self, dirname):
		fig, axes = plt.subplots(5, 1, sharex=True, figsize=(4, 5))
		x = list(range(len(self.workloadinfo)))
		for i,metric in enumerate(['totalcontainers', 'newcontainers', 'deployed', 'migrations', 'inqueue']):
			metric_with_interval = [self.workloadinfo[i][metric] for i in range(len(self.workloadinfo))]
			axes[i].plot(x, metric_with_interval)
			axes[i].set_ylabel(metric)
			axes[i].grid(b=True, which='both', color='#eeeeee', linestyle='-')
		plt.tight_layout(pad=0)
		plt.savefig(dirname + '/' + 'Workload' + '.pdf')

	########################################################################################################

	def generateCompleteDataset(self, dirname, data, name):
		title = name + '_with_interval' 
		metric_with_interval = []
		headers = list(data[0].keys())
		for datum in data:
			metric_with_interval.append([datum[value] for value in datum.keys()])
		df = pd.DataFrame(metric_with_interval, columns=headers)
		df.to_csv(dirname + '/' + title + '.csv', index=False)

	def generateDatasetWithInterval(self, dirname, metric, objfunc, metric2=None, objfunc2=None):
		title = metric + '_' + (metric2 + '_' if metric2 else "") + (objfunc + '_' if objfunc else "") + (objfunc2 + '_' if objfunc2 else "") + 'with_interval' 
		totalIntervals = len(self.hostinfo)
		metric_with_interval = []; metric2_with_interval = [] # metric1 is of host and metric2 is of containers
		host_alloc_with_interval = []; objfunc2_with_interval = []
		objfunc_with_interval = []
		for interval in range(totalIntervals-1):
			metric_with_interval.append([self.hostinfo[interval][metric][hostID] for hostID in range(len(self.hostinfo[0][metric]))])
			host_alloc_with_interval.append([self.activecontainerinfo[interval]['hostalloc'][cID] for cID in range(len(self.activecontainerinfo[0]['hostalloc']))])
			objfunc_with_interval.append(self.metrics[interval+1][objfunc])
			if metric2:
				metric2_with_interval.append(self.activecontainerinfo[interval][metric2])
			if objfunc2:
				objfunc2_with_interval.append(self.metrics[interval+1][objfunc2])
		df = pd.DataFrame(metric_with_interval)
		if metric2: df = pd.concat([df, pd.DataFrame(metric2_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(host_alloc_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(objfunc_with_interval)], axis=1)
		if objfunc2: df = pd.concat([df, pd.DataFrame(objfunc2_with_interval)], axis=1)
		df.to_csv(dirname + '/' + title + '.csv' , header=False, index=False)

	def generateDatasetWithInterval2(self, dirname, metric, metric2, metric3, metric4, objfunc, objfunc2):
		title = metric + '_' + metric2 + '_'  + metric3 + '_'  + metric4 + '_'  +objfunc + '_' + objfunc2 + '_' + 'with_interval' 
		totalIntervals = len(self.hostinfo)
		metric_with_interval = []; metric2_with_interval = [] 
		metric3_with_interval = []; metric4_with_interval = []
		host_alloc_with_interval = []; objfunc2_with_interval = []
		objfunc_with_interval = []
		for interval in range(totalIntervals-1):
			metric_with_interval.append([self.hostinfo[interval][metric][hostID] for hostID in range(len(self.hostinfo[0][metric]))])
			host_alloc_with_interval.append([self.activecontainerinfo[interval]['hostalloc'][cID] for cID in range(len(self.activecontainerinfo[0]['hostalloc']))])
			objfunc_with_interval.append(self.metrics[interval+1][objfunc])
			metric2_with_interval.append(self.activecontainerinfo[interval][metric2])
			metric3_with_interval.append(self.metrics[interval][metric3])
			metric4_with_interval.append(self.metrics[interval][metric4])
			objfunc2_with_interval.append(self.metrics[interval+1][objfunc2])
		df = pd.DataFrame(metric_with_interval)
		df = pd.concat([df, pd.DataFrame(metric2_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(host_alloc_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(metric3_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(metric4_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(objfunc_with_interval)], axis=1)
		df = pd.concat([df, pd.DataFrame(objfunc2_with_interval)], axis=1)
		df.to_csv(dirname + '/' + title + '.csv' , header=False, index=False)

	def generateGraphs(self, dirname):
		self.generateGraphsWithInterval(dirname, self.hostinfo, 'host', 'cpu')
		self.generateGraphsWithInterval(dirname, self.hostinfo, 'host', 'numcontainers')
		self.generateGraphsWithInterval(dirname, self.hostinfo, 'host', 'power')
		self.generateGraphsWithInterval(dirname, self.hostinfo, 'host', 'baseips', 'apparentips')
		self.generateGraphsWithInterval(dirname, self.hostinfo, 'host', 'ipscap', 'apparentips')
		self.generateGraphsWithInterval(dirname, self.activecontainerinfo, 'container', 'ips', 'apparentips')
		self.generateGraphsWithInterval(dirname, self.activecontainerinfo, 'container', 'hostalloc')
		self.generateMetricsWithInterval(dirname)
		self.generateWorkloadWithInterval(dirname)

	def generateDatasets(self, dirname):
		# self.generateDatasetWithInterval(dirname, 'cpu', objfunc='energytotalinterval')
		self.generateDatasetWithInterval(dirname, 'cpu', metric2='apparentips', objfunc='energytotalinterval', objfunc2='avgresponsetime')

		# We do not run GOBI prediction so comment it out
		# self.generateDatasetWithInterval2(dirname, 'cpu', 'apparentips', 'energytotalinterval_pred', 'avgresponsetime_pred', objfunc='energytotalinterval', objfunc2='avgresponsetime')
		
	def generateCompleteDatasets(self, dirname):
		self.generateCompleteDataset(dirname, self.hostinfo, 'hostinfo')
		self.generateCompleteDataset(dirname, self.workloadinfo, 'workloadinfo')
		self.generateCompleteDataset(dirname, self.metrics, 'metrics')
		self.generateCompleteDataset(dirname, self.activecontainerinfo, 'activecontainerinfo')
		self.generateCompleteDataset(dirname, self.allcontainerinfo, 'allcontainerinfo')
		self.generateCompleteDataset(dirname, self.schedulerinfo, 'schedulerinfo')