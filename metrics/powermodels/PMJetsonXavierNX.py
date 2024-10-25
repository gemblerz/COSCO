from .PM import *
import math

class PMJetsonXavierNX(PM):
	def __init__(self):
		super().__init__()
		# [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
		self.powerlist = list(range(5, 16))

	# cpu consumption in 100
	def power(self):
		cpu = self.host.getCPU()
		index = math.floor(cpu / 10)
		left = self.powerlist[index]
		right = self.powerlist[index + 1 if cpu%10 != 0 else index]
		alpha = (cpu / 10) - index
		return alpha * right + (1 - alpha) * left