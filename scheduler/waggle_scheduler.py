from .Scheduler import *
import numpy as np
import logging as logger
from copy import deepcopy


class WaggleScheduler(Scheduler):
    
    # Objective function to be minimized (probably eventually move this to the yaml)
    # policy indicates the decision variable, written as an N by M array, where
    # policy[i,t] is the number of jobs of type t allocated to node i
    #
    # alpha is a scalar between 0 & 1, a tunable parameter for alpha fairness.
    # 
    # power is the vector of powers needed for each job (power[t] is the power for that task)
    # 
    # state indicates the current job allocation right before schedulling as an N by M array,
    # i.e., state[i,t] is the power allocated to task(s) t at node i. In terms of the writeup,
    # state[i,t] at time k = x_i^t(k-1) - O_i^t(k)
    def objective(policy,alpha,power,state)
        X = sum(policy*power + state, axis=0)
        return sum(X^(1-alpha)/(1-alpha))
    
    def __init__(self):
        super().__init__()

    def selection(self):
        return self.RandomContainerSelection()

    def placement(self, containerIDs):
        # For debugging purpose, printing the first host's (node) group ID
        print(f'group ID of the first host is {self.env.hostlist[0].group}')
        return self.FirstFitPlacement(containerIDs)
