# To check if in Standby
import Screens.Standby

# Timer, eServiceReference
from enigma import eTimer, eServiceReference

# Check if in timespan, calculate timer durations
from time import localtime, mktime, time

# Path (check if file exists, getmtime)
from os import path

# We want a list of unique services
from sets import Set

# Configuration
from Components.config import config

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
		self.timer_mode = "wait"
		self.forcedScan = False

		# Mtime of configuration files
		self.configMtime = -1

		# Read in Configuration
		self.readConfiguration()

	def readConfiguration(self):
		# Check if file exists
		if not path.exists(CONFIG):
			return

		# Check if file did not change
		mtime = path.getmtime(CONFIG)
		if mtime == self.configMtime:
			return

		# Keep mtime
		self.configMtime = mtime

		# Empty out list
		self.services.clear()

		# Open file
		file = open(CONFIG, 'r')

		# Add References
		for line in file:
			line = line.strip()
			if line:
				self.services.add(line)

		# Close file
		file.close()

	def saveConfiguration(self):
		# Open file
		file = open(CONFIG, 'w')

		# Write references
		for serviceref in self.services:
			file.write(serviceref)
			file.write('\n')

		# Close file
		file.close()

	def refresh(self):
		print "[EPGRefresh] Forcing start of EPGRefresh"
		self.timer.stop()
		self.timer_mode = "refresh"
		self.forcedScan = True
		self.prepareRefresh()

	def start(self):
		# Don't abort a running forced scan, it will set the timer itself
		if self.forcedScan:
			return

		# Calculate unix timestamp of begin of timespan
		begin = [x for x in localtime()]
		begin[3] = config.plugins.epgrefresh.begin.value[0]
		begin[4] = config.plugins.epgrefresh.begin.value[1]
		begin = mktime(begin)

		# Calculate difference
		delay = begin-time()

		# Wait at least 3 seconds
		if delay < 3:
			delay = 3

		# debug, start timer
		print '[EPGRefresh] Timer will fire for the first time in %d seconds' % (delay) 
		self.timer.startLongTimer(int(delay))

	def stop(self):
		print "[EPGRefresh] Stopping Timer"
		self.timer.stop()
		self.timer_mode = "wait"

	def checkTimespan(self, begin, end):
		# Get current time
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

	def prepareRefresh(self):
		print "[EPGRefresh] About to start refreshing EPG"
		# Keep service
		from NavigationInstance import instance as nav
		self.previousService =  nav.getCurrentlyPlayingServiceReference()

		# Maybe read in configuration
		try:
			self.readConfiguration()
		except Exception, e:
			print "[EPGRefresh] Error occured while reading in configuration:", e

		# Save Services in a dict <transponder data> => serviceref
		scanServices = {}

		# TODO: does this really work?
		for serviceref in self.services:
			service = eServiceReference(serviceref)
			channelID = '%08x%04x%04x' % (
				service.getUnsignedData(4), # NAMESPACE
				service.getUnsignedData(2), # TSID
				service.getUnsignedData(3), # ONID
			)
			if not scanServices.has_key(channelID):
				scanServices[channelID] = service

		# See if we are supposed to read in autotimer services
		if config.plugins.epgrefresh.inherit_autotimer.value:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer

				# See if instance is empty
				if autotimer is None:
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()

				# Read in configuration
				autotimer.readXml()

				# Fetch services
				for timer in autotimer.getEnabledTimerList():
					for serviceref in timer.getServices():
						service = eServiceReference(str(serviceref))
						channelID = '%08x%04x%04x' % (
							service.getUnsignedData(4), # NAMESPACE
							service.getUnsignedData(2), # TSID
							service.getUnsignedData(3), # ONID
						)
						if not scanServices.has_key(channelID):
							scanServices[channelID] = service
			except Exception, e:
				print "[EPGRefresh] Could not inherit AutoTimer Services:", e

		# Make a list of services
		self.scanServices = scanServices.values()

		# Debug
		from ServiceReference import ServiceReference
		print "[EPGRefresh] Services we're going to scan:", ', '.join([ServiceReference(x).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '') for x in self.scanServices])

		self.timer_mode = "refresh"
		self.timeout()

	def cleanUp(self):
		# We need nav
		from NavigationInstance import instance as nav

		# shutdown if we're supposed to go to deepstandby and not recording
		# TODO: improve this (we might no longer be in standby (general problem), recordings might not be running but about to start)
		if not self.forcedScan and config.plugins.epgrefresh.afterevent.value and Screens.Standby.inStandby and not nav.RecordTimer.isRecording():
			from enigma import quitMainloop
			quitMainloop(1)

		# Reset status
		self.timer_mode = "wait"
		self.forcedScan = False

		# Zap back
		if self.previousService is not None or Screens.Standby.inStandby:
			nav.playService(self.previousService)

		# Wait at least until out of timespan again
		diff = abs(config.plugins.epgrefresh.begin.value[0]-config.plugins.epgrefresh.end.value[0])+1
		delay = diff*3600

		# debug, start timer
		print '[EPGRefresh] Timer will fire again in %d seconds' % (delay) 
		self.timer.startLongTimer(int(delay))

	def timeout(self):
		# Walk Services
		if self.timer_mode == "refresh":
			if self.forcedScan or config.plugins.epgrefresh.force.value or (Screens.Standby.inStandby and not nav.RecordTimer.isRecording()):
				self.nextService()
			else:
				# We don't follow our rules here - If the Box is still in Standby and not recording we won't reach this line 
				if self.checkTimespan(config.plugins.epgrefresh.begin.value, config.plugins.epgrefresh.end.value):
					print "[EPGRefresh] Gone out of timespan while refreshing, sorry!"
					self.cleanUp()
				else:
					print "[EPGRefresh] Box no longer in Standby or Recording started, rescheduling"

					# Recheck later
					self.timer.startLongTimer(config.plugins.epgrefresh.delay_standby.value*60)

		# Pending for activation
		elif self.timer_mode == "wait":
			# Check if in timespan
			if self.checkTimespan(config.plugins.epgrefresh.begin.value, config.plugins.epgrefresh.end.value):
				print "[EPGRefresh] In Timespan, will check if we're in Standby and have no Recordings running next"
				# Do we realy want to check nav?
				from NavigationInstance import instance as nav
				if config.plugins.autotimer.force.value or (Screens.Standby.inStandby and not nav.RecordTimer.isRecording()):
					self.prepareRefresh()
				else:
					print "[EPGRefresh] Box still in use, rescheduling"	

					# Recheck later
					self.timer.startLongTimer(config.plugins.epgrefresh.delay_standby.value*60)
			else:
				print "[EPGRefresh] Not in timespan, rescheduling"

				# Recheck later
				self.timer.startLongTimer(config.plugins.epgrefresh.delay_timespan.value*60)
		# Corrupted ?!
		else:
			print "[EPGRefresh] Invalid status reached:", self.timer_mode
			self.timer_mode = "wait"
			self.timeout()

	def nextService(self):
		# DEBUG
		print "[EPGRefresh] Maybe zap to next service"

		# Check if more Services present
		if len(self.scanServices):
			# Get next reference
			service = self.scanServices.pop()

			# Play next service
			from NavigationInstance import instance as nav
			nav.playService(service)

			# Start Timer
			self.timer.startLongTimer(config.plugins.epgrefresh.interval.value*60)
		else:
			# Debug
			print "[EPGRefresh] Done refreshing EPG"

			# Clean up
			self.cleanUp()

epgrefresh = EPGRefresh()