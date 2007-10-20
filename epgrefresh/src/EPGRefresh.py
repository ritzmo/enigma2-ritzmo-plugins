# Standby
from Screens.Standby import inStandby

from enigma import eTimer, eServiceReference

from time import localtime

# Used during development to override standby check
FORCE_RUN_PLUGIN=True

# Duration to reside on service in s (to be configurable)
DURATION = 12

class EPGRefresh:
	"""WIP - Simple Class to refresh EPGData - WIP"""

	def __init__(self):
		# Initialize Timer
		self.timer = eTimer()
		self.timer.timeout.get().append(self.timeout)

		# Initialize 
		self.previousService = None
		self.position = -1
		self.timer_mode = 0

		# TODO: make this dynamic
		self.services = [
			eServiceReference(x)
			  for x in [
				  "1:0:1:6DCA:44D:1:C00000:0:0:0:",
				  "1:0:1:6D66:437:1:C00000:0:0:0:",
				  "1:0:1:445C:453:1:C00000:0:0:0:",
				  "1:0:1:2EE3:441:1:C00000:0:0:0:"
			  ]
		]

	def refresh(self):
		print "SCHEDULING TIMER TO FIRE IN 3s"
		self.timer.startLongTimer(3)

	def timeout(self):
		# Walk Services
		if self.timer_mode == 3:
			self.nextService()
		# Pending for activation
		elif self.timer_mode == 0:
			now = localtime() # 3 is h, 4 is m

			# Check if in timespan
			if FORCE_RUN_PLUGIN or (now[3] > 20 or (now[3] == 20 and now[4] >= 15) and now[3] < 6 or (now[3] == 6 and now[4] <= 30)):
				print "IN TIMESPAN"
				self.timer_mode = 1
				self.timeout()
			else:
				print "NOT IN TIMESPAN"
				# Recheck in 1h
				self.timer.startLongTimer(3600)
		# Check if in Standby
		elif self.timer_mode == 1:
			# Do we realy want to check nav?
			from NavigationInstance import instance as nav
			if (inStandby and not nav.isRecording()) or FORCE_RUN_PLUGIN:
				print "STANDBY AND NOT RECORDING"
				self.timer_mode = 2
				self.timeout()
			else:
				print "NOT STANDBY OR RECORDING"
				# Recheck in 10min
				self.timer.startLongtimer(600)
		# Reset Values
		elif self.timer_mode == 2:
			print "INITIALIZING"
			# Reset Position
			self.position = -1

			# Keep service
			from NavigationInstance import instance as nav
			self.previousService =  nav.getCurrentlyPlayingServiceReference()

			self.timer_mode = 3
			self.timeout()
		# Play old service, restart timer
		elif self.timer_mode == 4:
			print "FINISHED"
			self.timer_mode = 1

			# Zap back
			from NavigationInstance import instance as nav
			nav.playService(self.previousService)

			# Run in 2h again.
			# TODO: calculate s until next timespan begins 
			self.timer.startLongTimer(7200)

	def nextService(self):
		# Increment Position
		self.position += 1

		# DEBUG
		print "TRYING TO POLL NEXT SERVICE", self.position

		# Check if more Services present
		# TODO: cache length?!
		if len(self.services) > self.position:
			from NavigationInstance import instance as nav

			# Play next service
			nav.playService(self.services[self.position])

			# Start Timer
			self.timer.startLongTimer(DURATION)
		else:
			# Destroy service
			self.timer_mode = 4
			self.timeout()

epgrefresh = EPGRefresh()