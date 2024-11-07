import os, sys, stat
import sys
import optparse
import logging as logger
import configparser
import pickle
import shutil
import sqlite3
import platform
import yaml
from time import time
from subprocess import call
from os import system, rename

# Framework imports
from framework.Framework import *
from framework.database.Database import *
from framework.datacenter.Datacenter_Setup import *
from framework.datacenter.Datacenter import *
from framework.workload.DeFogWorkload import *
from framework.workload.AIoTBenchWorkload import *

# Simulator imports
from simulator.Simulator import *
from simulator.environment.AzureFog import *
from simulator.environment.WaggleFog import *
from simulator.environment.BitbrainFog import *
from simulator.workload.BitbrainWorkload2 import *
from simulator.workload.Azure2017Workload import *
from simulator.workload.Azure2019Workload import *

# Scheduler imports
# from scheduler.IQR_MMT_Random import IQRMMTRScheduler
# from scheduler.MAD_MMT_Random import MADMMTRScheduler
# from scheduler.MAD_MC_Random import MADMCRScheduler
# from scheduler.LR_MMT_Random import LRMMTRScheduler
# from scheduler.Random_Random_FirstFit import RFScheduler
# from scheduler.Random_Random_LeastFull import RLScheduler
# from scheduler.RLR_MMT_Random import RLRMMTRScheduler
# from scheduler.Threshold_MC_Random import TMCRScheduler
# from scheduler.Random_Random_Random import RandomScheduler
# from scheduler.HGP_LBFGS import HGPScheduler
# from scheduler.GA import GAScheduler
# from scheduler.GOBI import GOBIScheduler
# from scheduler.GOBI2 import GOBI2Scheduler
# from scheduler.DRL import DRLScheduler
# from scheduler.DQL import DQLScheduler
# from scheduler.POND import PONDScheduler
# from scheduler.SOGOBI import SOGOBIScheduler
# from scheduler.SOGOBI2 import SOGOBI2Scheduler
# from scheduler.HGOBI import HGOBIScheduler
# from scheduler.HGOBI2 import HGOBI2Scheduler
# from scheduler.HSOGOBI import HSOGOBIScheduler
# from scheduler.HSOGOBI2 import HSOGOBI2Scheduler
from scheduler.waggle_scheduler import WaggleScheduler

# Auxiliary imports
from stats.Stats import *
from utils.Utils import *
from pdb import set_trace as bp

usage = "usage: python main.py -e <environment> -m <mode> # empty environment run simulator"

parser = optparse.OptionParser(usage=usage)
parser.add_option("-e", "--environment", action="store", dest="env", default="sim", 
					help="Environment is Sim, AWS, Openstack, Azure, VLAN, Vagrant, Waggle")
parser.add_option("-c", "--configuration", action="store", dest="config", default="", 
					help="Configurations in yaml for hosts, simulation, etc.")
parser.add_option("-w", "--workload", action="store", dest="workload", default="Bitbrain", 
					help="Workload is Bitbrain, Waggle")
parser.add_option("-m", "--mode", action="store", dest="mode", default="0", 
					help="Mode is 0 (Create and destroy), 1 (Create), 2 (No op), 3 (Destroy)")
opts, args = parser.parse_args()

# Global constants
NUM_SIM_STEPS = 20
HOSTS = 10 * 5 if opts.env == '' else 10
CONTAINERS = HOSTS
TOTAL_POWER = 1000
ROUTER_BW = 10000
INTERVAL_TIME = 300 # seconds
NEW_CONTAINERS = 0 if HOSTS == 10 else 5
DB_NAME = ''
DB_HOST = ''
DB_PORT = 0
HOSTS_IP = []
logFile = 'COSCO.log'

if len(sys.argv) > 1:
	with open(logFile, 'w'): os.utime(logFile, None)

def initalizeEnvironment(config, logger):
	# Initialize simple fog datacenter
	''' Can be SimpleFog, BitbrainFog, AzureFog // Datacenter '''
	config_env = config.env.lower()
	if config_env == "waggle":
		datacenter = WaggleFog(config.hosts)
	elif config_env != '':
		datacenter = Datacenter(HOSTS_IP, config.env, 'Virtual')
	else:
		datacenter = AzureFog(HOSTS)

	# Initialize workload
	''' Can be SWSD, BWGD2, Azure2017Workload, Azure2019Workload // DFW, AIoTW '''
	config_workload = config.workload.lower()
	if config_workload == 'bitbrain':
		workload = BWGD2(NEW_CONTAINERS, 1.5)
	elif config_workload != '':
		# NOTE: the following breaks because of the db
		workload = DFW(NEW_CONTAINERS, 1.5, db)
	else:
		workload = BWGD2(NEW_CONTAINERS, 1.5)
	hostlist = datacenter.generateHosts()

	# Initialize scheduler
	''' Can be LRMMTR, RF, RL, RM, Random, RLRMMTR, TMCR, TMMR, TMMTR, GA, GOBI (arg = 'energy_latency_'+str(HOSTS)) '''
	# scheduler = GOBIScheduler('energy_latency_'+str(HOSTS)) # GOBIScheduler('energy_latency_'+str(HOSTS))
	scheduler = WaggleScheduler()

	# Initialize Environment
	env = Simulator(TOTAL_POWER, ROUTER_BW, scheduler, CONTAINERS, INTERVAL_TIME, hostlist)
	# NOTE: we disable the framework environment for now
	# if env != '':
	# 	# Initialize the db
	# 	db = Database(DB_NAME, DB_HOST, DB_PORT)
	# 	env = Framework(scheduler, CONTAINERS, INTERVAL_TIME, hostlist, db, env, logger)
	# else:
	# 	env = Simulator(TOTAL_POWER, ROUTER_BW, scheduler, CONTAINERS, INTERVAL_TIME, hostlist)

	# Initialize stats
	stats = Stats(env, workload, datacenter, scheduler)

	# Execute first step
	newcontainerinfos = workload.generateNewContainers(env.interval) # New containers info
	deployed = env.addContainersInit(newcontainerinfos) # Deploy new containers and get container IDs
	start = time()
	decision = scheduler.placement(deployed) # Decide placement using container ids
	schedulingTime = time() - start
	migrations = env.allocateInit(decision) # Schedule containers
	workload.updateDeployedContainers(env.getCreationIDs(migrations, deployed)) # Update workload allocated using creation IDs
	print("Deployed containers' creation IDs:", env.getCreationIDs(migrations, deployed))
	print("Containers in host:", env.getContainersInHosts())
	print("Schedule:", env.getActiveContainerList())
	printDecisionAndMigrations(decision, migrations)

	stats.saveStats(deployed, migrations, [], deployed, decision, schedulingTime)
	return datacenter, workload, scheduler, env, stats


def stepSimulation(workload, scheduler, env, stats):
	# TODO: we neet to generate jobs based on scientific goals (user needs, etc), not just randomly
	# TODO: we need to associate each container (job) to a group to represent groups in
	#       the problem domain
	newcontainerinfos = workload.generateNewContainers(env.interval) # New containers info
	if opts.env != '': print(newcontainerinfos)
	deployed, destroyed = env.addContainers(newcontainerinfos) # Deploy new containers and get container IDs
	start = time()
	selected = scheduler.selection() # Select container IDs for migration
	decision = scheduler.filter_placement(scheduler.placement(selected+deployed)) # Decide placement for selected container ids
	schedulingTime = time() - start
	migrations = env.simulationStep(decision) # Schedule containers
	workload.updateDeployedContainers(env.getCreationIDs(migrations, deployed)) # Update workload deployed using creation IDs
	print("Deployed containers' creation IDs:", env.getCreationIDs(migrations, deployed))
	print("Deployed:", len(env.getCreationIDs(migrations, deployed)), "of", len(newcontainerinfos), [i[0] for i in newcontainerinfos])
	print("Destroyed:", len(destroyed), "of", env.getNumActiveContainers())
	print("Containers in host:", env.getContainersInHosts())
	print("Num active containers:", env.getNumActiveContainers())
	print("Host allocation:", [(c.getHostID() if c else -1)for c in env.containerlist])
	printDecisionAndMigrations(decision, migrations)

	stats.saveStats(deployed, migrations, destroyed, selected, decision, schedulingTime)


def saveStats(stats, datacenter, workload, env, end=True):
	dirname = "logs/" + datacenter.__class__.__name__
	dirname += "_" + workload.__class__.__name__
	dirname += "_" + str(NUM_SIM_STEPS) 
	dirname += "_" + str(HOSTS)
	dirname += "_" + str(CONTAINERS)
	dirname += "_" + str(TOTAL_POWER)
	dirname += "_" + str(ROUTER_BW)
	dirname += "_" + str(INTERVAL_TIME)
	dirname += "_" + str(NEW_CONTAINERS)
	if not os.path.exists("logs"): os.mkdir("logs")
	if os.path.exists(dirname): shutil.rmtree(dirname, ignore_errors=True)
	os.mkdir(dirname)
	stats.generateDatasets(dirname)
	if 'Datacenter' in datacenter.__class__.__name__:
		saved_env, saved_workload, saved_datacenter, saved_scheduler, saved_sim_scheduler = stats.env, stats.workload, stats.datacenter, stats.scheduler, stats.simulated_scheduler
		stats.env, stats.workload, stats.datacenter, stats.scheduler, stats.simulated_scheduler = None, None, None, None, None
		with open(dirname + '/' + dirname.split('/')[1] +'.pk', 'wb') as handle:
			pickle.dump(stats, handle)
		stats.env, stats.workload, stats.datacenter, stats.scheduler, stats.simulated_scheduler = saved_env, saved_workload, saved_datacenter, saved_scheduler, saved_sim_scheduler
	if not end: return
	stats.generateGraphs(dirname)
	stats.generateCompleteDatasets(dirname)
	stats.env, stats.workload, stats.datacenter, stats.scheduler = None, None, None, None
	if 'Datacenter' in datacenter.__class__.__name__:
		stats.simulated_scheduler = None
		logger.getLogger().handlers.clear(); env.logger.getLogger().handlers.clear()
		if os.path.exists(dirname+'/'+logFile): os.remove(dirname+'/'+logFile)
		rename(logFile, dirname+'/'+logFile)
	with open(dirname + '/' + dirname.split('/')[1] +'.pk', 'wb') as handle:
	    pickle.dump(stats, handle)


if __name__ == '__main__':
	logger.basicConfig(filename=logFile, level=logger.DEBUG,
		format='%(asctime)s - %(levelname)s - %(message)s')
	
	if opts.config != "":
		with open(opts.config, "r") as file:
			loaded_config = yaml.safe_load(file)
		config = dotdict(loaded_config)
	else:
		config = opts
	logger.info(f'configuration: {config}')

	if config.env == "waggle":
		pass
	elif config.env != '':
		# Convert all agent files to unix format
		unixify(['framework/agent/', 'framework/agent/scripts/'])

		# Start InfluxDB service
		print(color.HEADER+'InfluxDB service runs as a separate front-end window. Please minimize this window.'+color.ENDC)
		if 'Windows' in platform.system():
			os.startfile('C:/Program Files/InfluxDB/influxdb-1.8.3-1/influxd.exe')

		configFile = 'framework/config/' + opts.env + '_config.json'
		
		cfg = {}
		with open(configFile, "r") as f:
			cfg = json.load(f)
		DB_HOST = cfg['database']['ip']
		DB_PORT = cfg['database']['port']
		DB_NAME = 'COSCO'

		if config.env == 'Vagrant':
			print("Setting up VirtualBox environment using Vagrant")
			HOSTS_IP = setupVagrantEnvironment(configFile, config.mode)
			print(HOSTS_IP)
		elif config.env == 'VLAN':
			print("Setting up VLAN environment using Ansible")
			HOSTS_IP = setupVLANEnvironment(configFile, config.mode)
			print(HOSTS_IP)
		# exit()

	datacenter, workload, scheduler, env, stats = initalizeEnvironment(config, logger)

	for step in range(NUM_SIM_STEPS):
		print(color.BOLD+"Simulation Interval:", step, color.ENDC)
		stepSimulation(workload, scheduler, env, stats)
		if env != '' and step % 10 == 0: saveStats(stats, datacenter, workload, env, end = False)

	# NOTE: in a simulation mode, nothing should be destroyed.
	#    we simply comment this out for now.
	# if opts.env != '':
	# 	# Destroy environment if required
	# 	eval('destroy'+opts.env+'Environment(configFile, mode)')

	# 	# Quit InfluxDB
	# 	if 'Windows' in platform.system():
	# 		os.system('taskkill /f /im influxd.exe')

	saveStats(stats, datacenter, workload, env)

