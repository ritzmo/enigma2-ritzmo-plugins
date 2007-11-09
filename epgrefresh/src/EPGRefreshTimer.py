import timer
from time import localtime, mktime, time

class EPGRefreshTimerEntry(timer.TimerEntry):
	"""TimerEntry ..."""
	def __init__(self, begin, tocall):
		timer.TimerEntry.__init__(self, int(begin), int(begin))

		self.prepare_time = 0
		self.function = tocall

	def getNextActivation(self):
		return self.begin

	def activate(self):
		if self.state == self.StateRunning:
			self.function()

		return True

	def shouldSkip(self):
		return False

class EPGRefreshTimer(timer.Timer):
	def __init__(self):
		timer.Timer.__init__(self)
		self.refreshTimer = None

	def remove(self, entry):
		print "[EPGRefresh] Timer removed " + str(entry)

		# avoid re-enqueuing
		entry.repeated = False

		# abort timer.
		# this sets the end time to current time, so timer will be stopped.
		entry.abort()

		if entry.state != entry.StateEnded:
			self.timeChanged(entry)

		print "state: ", entry.state
		print "in processed: ", entry in self.processed_timers
		print "in running: ", entry in self.timer_list
		# now the timer should be in the processed_timers list. remove it from there.
		self.processed_timers.remove(entry)


	def addRefreshTimer(self, beginh, beginm, tocall):
		if self.refreshTimer is not None:
			self.remove(self.refreshTimer)

		# Calculate unix timestamp of begin of timespan
		begin = [x for x in localtime()]
		begin[3] = beginh
		begin[4] = beginm
		begin = mktime(begin)

		self.refreshTimer = EPGRefreshTimerEntry(begin, tocall)

		for x in range(0,7):
			self.refreshTimer.setRepeated(x)

		self.addTimerEntry(self.refreshTimer)

	def add(self, entry):
		entry.timeChanged()
		print "[EPGRefresh] Timer added " + str(entry)
		entry.Timer = self
		self.addTimerEntry(entry)

	def clear(self):
		self.timer_list = []

	def isActive(self):
		return self.refreshTimer is not None

epgrefreshtimer = EPGRefreshTimer()