from .Scheduler import *
import numpy as np
import logging as logger
from copy import deepcopy


class WaggleScheduler(Scheduler):
    def __init__(self):
        super().__init__()

    def selection(self):
        return self.RandomContainerSelection()

    def placement(self, containerIDs):
        # For debugging purpose, printing the first host's (node) group ID
        print(f'group ID of the first host is {self.env.hostlist[0].group}')
        return self.FirstFitPlacement(containerIDs)
