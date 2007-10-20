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

	def refresh(self):
		print "[EPGRefresh] Timer will fire for the first time in 3 seconds"
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
			if (inStandby and not nav.isRecording()) or FORCE_RUN_PLUGIN:
				self.timer_mode = 2
				self.timeout()
			else:
				print "[EPGRefresh] Box still in use, rescheduling"
				# Recheck in 10min
				self.timer.startLongtimer(600)
		# Reset Values
		elif self.timer_mode == 2:
			print "[EPGRefresh] About to start refreshing epg"
			# Keep service
			from NavigationInstance import instance as nav
			self.previousService =  nav.getCurrentlyPlayingServiceReference()

			self.scanServices = self.services.copy()
			if config.plugins.epgrefresh.inherit_autotimer.value:
				try:
					from Plugins.Extensions.AutoTimer.plugin import autotimer
					if autotimer is None:
						from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
						autotimer = AutoTimer(session)
						autotimer.readXml()
					
					for timer in autotimer.getEnabledTimerList():
						self.scanServices = self.scanServices.union(Set(timer.getServices()))
				except Exception, e:
					print "[EPGRefresh] Could not inherit AutoTimer Services:", e

			print "[EPGRefresh] Services we're going to scan:", self.scanServices

			self.timer_mode = 3
			self.timeout()
		# Play old service, restart timer
		elif self.timer_mode == 4:
			print "[EPGRefresh] Done refreshing epg"
			self.timer_mode = 1

			# Zap back
			from NavigationInstance import instance as nav
			nav.playService(self.previousService)

			# Run in 2h again.
			# TODO: calculate s until next timespan begins 
			self.timer.startLongTimer(7200)

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