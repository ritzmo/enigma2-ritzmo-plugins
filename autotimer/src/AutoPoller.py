# Timer
from enigma import eTimer

# Interval in s, to be configurable
INTERVAL = 10800

class AutoPoller:
	def __init__(self):
		# Init Timer
		self.timer = eTimer()
		self.timer.timeout.get().append(self.query)

	def start(self, autotimer):
		self.autotimer = autotimer
		self.timer.start(10, True)

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