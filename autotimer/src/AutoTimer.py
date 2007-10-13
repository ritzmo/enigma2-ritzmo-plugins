# Config
from xml.dom.minidom import parse as minidom_parse
from Tools.Directories import fileExists

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, parseEvent

# Timespan
from time import localtime, mktime

# EPGCache & Event
from enigma import eEPGCache, eServiceReference

XML_CONFIG = "/etc/enigma2/autotimer.xml"

class AutoTimer:
	def __init__(self, session):
		# Save session (somehow NavigationInstance.instance is None ?!)
		self.session = session

		# Keep EPGCache
		self.epgcache = eEPGCache.getInstance()

		# Initialize Timers
		self.timers = []

		# Parse config
		self.readXml()
		print "[AutoTimer] Generated List", self.timers

	def getValue(self, definitions, default, isList = True):
		# Initialize Output
		ret = ""

		# How many definitions are present
		if isList:
			Len = len(definitions)
			if Len > 0:
				childNodes = definitions[Len-1].childNodes
			else:
				childNodes = []
		else:
			childNodes = definitions.childNodes

		# Iterate through nodes of last one
		for node in childNodes:
			# Append text if we have a text node
			if node.nodeType == node.TEXT_NODE:
				ret = ret + node.data

		# If output is still empty return default
		if not len(ret):
			return default

		# Otherwise return output
		return ret

	def readXml(self):
		# Empty out timers
		del self.timers[:]

		# Abort if no config found
		if not fileExists(XML_CONFIG):
			return

		# Parse Config
		dom = minidom_parse(XML_CONFIG)

		# Get Config Element
		for config in dom.getElementsByTagName("autotimer"):
			# Iterate Timers
			for timer in config.getElementsByTagName("timer"):
				# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None)

				# Read out name
				name = self.getValue(timer.getElementsByTagName("name"), None)
				if name is None:
					print "[AutoTimer] Erroneous config, skipping entry"
					continue

				# Guess allowedtime
				allowed = timer.getElementsByTagName("timespan")
				if len(allowed):
					# We only support 1 Timespan so far
					start = self.getValue(allowed[0].getElementsByTagName("from"), None)
					end = self.getValue(allowed[0].getElementsByTagName("to"), None)
					if start and end:
						timetuple = (start, end)
					else:
						timetuple = None
				else:
					timetuple = None

				# Read out allowed services
				allowed = timer.getElementsByTagName("serviceref")
				if len(allowed):
					servicelist = []
					for service in allowed:
						value = self.getValue(service, None, False)
						if value:
							servicelist.append(value)
					if not len(servicelist):
						servicelist = None
				else:
					servicelist = None

				# Finally append tuple
				self.timers.append((
						str(name),
						timetuple,
						servicelist
				))

	def set(self, name, tuple):
		idx = 0
		for timer in self.timers:
			if timer[0] == name:
				self.timers[idx] = tuple
				return
			idx += 1
		self.timers.append(tuple)

	def remove(self, name):
		idx = 0
		for timer in self.timers:
			if timer[0] == name:
				self.timers.pop(idx)
				return

	def writeXml(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<autotimer>\n']

		# Iterate timers
		for timer in self.timers:
			list.append(' <timer>\n')
			list.append(''.join(['  <name>', timer[0], '</name>\n']))
			if timer[1] is not None:
				list.append('  <timespan>\n')
				list.append(''.join(['   <from>', timer[1][0], '</from>\n']))
				list.append(''.join(['   <to>', timer[1][1], '</to>\n']))
				list.append('  </timespan>\n')
			if timer[2] is not None:
				for serviceref in timer[2]:
					list.append(''.join(['  <serviceref>', serviceref, '</serviceref>\n']))
			list.append(' </timer>\n')
		list.append('</autotimer>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_CONFIG, "w")
			file.writelines(list)
		except Exception, e:
			print "[AutoTimer] Error Saving Timer List:", e
		finally:
			if file is not None:
				file.close()

	def parseEPG(self):
		new = 0
		skipped = 0

		# Iterate Timer
		for timer in self.timers:
			try:
				# Search EPG
				ret = self.epgcache.search(('RIBD', 100, eEPGCache.PARTIAL_TITLE_SEARCH, timer[0], eEPGCache.NO_CASE_CHECK))

				# Continue on empty result
				if ret is None:
					print "[AutoTimer] Got empty result"
					continue

				for event in ret:
					# Format is (ServiceRef, EventId, BeginTime, Duration)
					# Example: ('1:0:1:445D:453:1:C00000:0:0:0:', 25971L, 1192287455L, 600L)
					print "[AutoTimer] Checking Tuple:", event

					# Check if we have Timelimit
					if timer[1] is not None:
						# From
						tuple = timer[1][0].split(':')
						begin = [x for x in localtime(event[2])]
						begin[3] = int(tuple[0])
						begin[4] = int(tuple[1]) 

						# To
						tuple = timer[1][1].split(':')
						end = [x for x in localtime(event[2] + event[3])]
						end[3] = int(tuple[0])
						end[4] = int(tuple[1])

						# Convert back
						begin = mktime(begin)
						end = mktime(end)

						# Continue if not in Range
						if begin > event[2] or end < event[2] + event[3]:
							continue

					# Check if we have Servicelimit
					if timer[2] is not None:
						# Continue if service not allowed
						if event[0] not in timer[2]:
							continue

					ref = eServiceReference(event[0])
					evt = self.epgcache.lookupEventId(ref, event[1])
					if evt:							
						# Check for double Timers
						unique = True
						for rtimer in self.session.nav.RecordTimer.timer_list:
							# Serviceref equals and begin is only 10min different
							# TODO: improve check (eventId would be handy)
							if str(rtimer.service_ref) == event[0] and abs(rtimer.begin - event[2]) < 600:
								print "[AutoTimer] Event already scheduled."
								unique = False
								skipped += 1
								break

						# If timer is "unique"
						if unique:
							print "[AutoTimer] Adding this event."
							newEntry = RecordTimerEntry(ServiceReference(ref), *parseEvent(evt))
							self.session.nav.RecordTimer.record(newEntry)
							new += 1
					else:
						print "[AutoTimer] Could not create Event!"

			except StandardError, se:
				print "[AutoTimer] Error occured:", se

		return (new, skipped)