from .Scheduler import *
import numpy as np
import logging as logger
from copy import deepcopy


class WaggleScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        # We need a network model (matrix) where i, j represents the connection from node i to node j
        # self.network_metrix = [[]]
        # self.conf = [0, 0, 0]

    def selection(self):
        return self.RandomContainerSelection()

    def placement(self, containerIDs):
        # For debugging purpose, printing the first host's (node) group ID
        print(f'group ID of the first host is {self.env.hostlist[0].group}')
        # self.conf[2] += 0.5
        return self.RandomPlacement(containerIDs)
