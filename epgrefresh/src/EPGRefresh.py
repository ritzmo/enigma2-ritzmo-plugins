# Standby
from Screens.Standby import inStandby

from enigma import eTimer, eServiceReference

from time import localtime

from os import path

from sets import Set

from Components.config import config

# Used during development to override standby check
FORCE_RUN_PLUGIN=True

# Path to configuration
CONFIG = "/etc/enigma2/epgrefresh.conf"

class EPGRefresh:
	"""WIP - Simple Class to refresh EPGData - WIP"""

	def __init__(self):
		# Initialize Timer
		self.timer = eTimer()
		self.timer.timeout.get().append(self.timeout)

		# Initialize 
		self.services = Set()
		self.previousService = None
		self.timer_mode = 0

		# Mtime of configuration files
		self.configMtime = -1

		# Read in Configuration
		self.readConfiguration()

	def readConfiguration(self):
		if not path.exists(CONFIG):
			return

		mtime = path.getmtime(CONFIG)
		if mtime == self.configMtime:
			return

		self.configMtime = mtime

		del self.services[:]
		file = open(CONFIG, 'r')
		for line in file:
			self.services.add(line)
		file.close()

	def saveConfigurtion(self):
		file = open(CONFIG, 'w')
		for serviceref in self.services:
			file.write(serviceref)
		file.close()

	def start(self):
		print "[EPGRefresh] Timer will fire for the first time in 3 seconds"
		self.timer.startLongTimer(3)

	def stop(self):
		print "[EPGRefresh] Stopping Timer"
		self.timer.stop()

	def checkTimespan(self, begin, end):
		time = localtime()

		# Check if we span a day
		if begin[0] > end[0] or (begin[0] == end[0] and begin[1] >= end[1]):
			# Check if begin of event is later than our timespan starts
			if time[3] > begin[0] or (time[3] == begin[0] and time[4] >= begin[1]):
				# If so, event is in our timespan
				return True
			# Check if begin of event is earlier than our timespan end
			if time[3] < end[0] or (time[3] == end[0] and time[4] <= end[1]):
				# If so, event is in our timespan
				return True
			return False
		else:
			# Check if event begins earlier than our timespan starts 
			if time[3] < begin[0] or (time[3] == begin[0] and time[4] <= begin[1]):
				# Its out of our timespan then
				return False
			# Check if event begins later than our timespan ends
			if time[3] > end[0] or (time[3] == end[0] and time[4] >= end[1]):
				# Its out of our timespan then
				return False
			return True

	def timeout(self):
		# Walk Services
		if self.timer_mode == 3:
			self.nextService()

		# Pending for activation
		elif self.timer_mode == 0:
			# Check if in timespan
			if FORCE_RUN_PLUGIN or self.checkTimespan(config.plugins.epgrefresh.begin.value, config.plugins.epgrefresh.end.value):
				self.timer_mode = 1
				self.timeout()
			else:
				print "[EPGRefresh] Not in timespan, rescheduling"
				# Recheck in 1h
				self.timer.startLongTimer(3600)

		# Check if in Standby
		elif self.timer_mode == 1:
			# Do we realy want to check nav?
			from NavigationInstance import instance as nav
			if FORCE_RUN_PLUGIN or (inStandby and not nav.isRecording()):
				self.timer_mode = 2
				self.timeout()
			else:
				print "[EPGRefresh] Box still in use, rescheduling"
				# Recheck in 10min
				self.timer.startLongtimer(600)

		# Reset Values
		elif self.timer_mode == 2:
			print "[EPGRefresh] About to start refreshing EPG"
			# Keep service
			from NavigationInstance import instance as nav
			self.previousService =  nav.getCurrentlyPlayingServiceReference()

			try:
				self.readConfiguration()
			except Exception, e:
				print "[EPGRefresh] Error occured while reading in configuration:", e

			self.scanServices = self.services.copy()
			if config.plugins.epgrefresh.inherit_autotimer.value:
				try:
					from Plugins.Extensions.AutoTimer.plugin import autotimer
					if autotimer is None:
						from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
						autotimer = AutoTimer(None)
						autotimer.readXml()
						list = autotimer.getEnabledTimerList()
						autotimer = None
					else:
						# TODO: force parsing?
						list = autotimer.getEnabledTimerList()
					
					for timer in list:
						self.scanServices = self.scanServices.union(Set(timer.getServices()))
				except Exception, e:
					print "[EPGRefresh] Could not inherit AutoTimer Services:", e

			print "[EPGRefresh] Services we're going to scan:", self.scanServices

			self.timer_mode = 3
			self.timeout()

		# Play old service, restart timer
		elif self.timer_mode == 4:
			print "[EPGRefresh] Done refreshing EPG"
			self.timer_mode = 1

			# Zap back
			from NavigationInstance import instance as nav
			nav.playService(self.previousService)

			# Run in 2h again.
			# TODO: calculate s until next timespan begins 
			self.timer.startLongTimer(7200)
		# Corrupted ?!
		else:
			print "[EPGRefresh] Invalid status reached:", self.timer_mode
			self.timer_move = 1
			self.timeout()

	def nextService(self):
		# DEBUG
		print "[EPGRefresh] Maybe zap to next service"

		# Check if more Services present
		if len(self.scanServices):
			serviceref = self.scanServices.pop()

			from NavigationInstance import instance as nav

			# Play next service
			nav.playService(eServiceReference(str(serviceref)))

			# Start Timer
			self.timer.startLongTimer(config.plugins.epgrefresh.interval.value*60)
		else:
			# Destroy service
			self.timer_mode = 4
			self.timeout()

epgrefresh = EPGRefresh()