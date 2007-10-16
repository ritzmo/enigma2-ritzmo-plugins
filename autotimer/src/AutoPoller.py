# Timer
from enigma import eTimer

# Interval in s, to be configurable
INTERVAL = 10800

class AutoPoller:
	def __init__(self):
		# Keep track if we were launched before
		self.shouldRun = False

		# Init Timer
		self.timer = eTimer()
		self.timer.timeout.get().append(self.query)

	def start(self, autotimer, initial = True):
		self.autotimer = autotimer
		self.shouldRun = True
		if initial:
			delay = 2
		else:
			delay = INTERVAL
		self.timer.startLongTimer(delay)

	def stop(self):
		self.timer.stop()

	def query(self):
		# Ignore any exceptions
		try:
			self.autotimer.parseEPG()
		except:
			pass

		self.timer.startLongTimer(INTERVAL)

autopoller = AutoPoller()