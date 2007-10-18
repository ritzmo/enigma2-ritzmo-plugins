# Plugins Config
from xml.dom.minidom import parse as minidom_parse
from os import path as os_path

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT

# Timespan
from time import localtime, mktime, time

# EPGCache & Event
from enigma import eEPGCache, eServiceReference

# Enigma2 Config (Timermargin)
from Components.config import config

# AutoTimer Component
from AutoTimerComponent import AutoTimerComponent

XML_CONFIG = "/etc/enigma2/autotimer.xml"
CURRENT_CONFIG_VERSION = "2"

def getValue(definitions, default, isList = True):
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
	ret = ret.strip()
	if not len(ret):
		return default

	# Otherwise return output
	return ret

class AutoTimer:
	def __init__(self, session):
		# Save session (somehow NavigationInstance.instance is None ?!)
		self.session = session

		# Keep EPGCache
		self.epgcache = eEPGCache.getInstance()

		# Initialize Timers
		self.timers = []

		# Empty mtime
		self.configMtime = 0

	def readXml(self, mtime = None):
		# Empty out timers and reset Ids
		del self.timers[:]
		self.uniqueTimerId = 0

		# Abort if no config found
		if not os_path.exists(XML_CONFIG):
			return

		# Save mtime
		if not mtime:
			self.configMtime = os_path.getmtime(XML_CONFIG)
		else:
			self.configMtime = mtime

		# Parse Config
		dom = minidom_parse(XML_CONFIG)

		# Get Config Element
		for config in dom.getElementsByTagName("autotimer"):
			# Parse old configuration files
			if config.getAttribute("version") != CURRENT_CONFIG_VERSION:
				from OldConfigurationParser import parseConfig
				parseConfig(config, self.timers, config.getAttribute("version"))
				self.uniqueTimerId = len(self.timers)
				continue
			# Iterate Timers
			for timer in config.getElementsByTagName("timer"):
				# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None, timeoffset in m (before, after) or None, afterevent)

				# Increment uniqueTimerId
				self.uniqueTimerId += 1

				# Read out name
				name = timer.getAttribute("name")
				if name is None:
					print '[AutoTimer] Erroneous config is missing attribute "name", skipping entry'
					continue

				enabled = timer.getAttribute("enabled") or "yes"
				if enabled == "no":
					enabled = False
				elif enabled == "yes":
					enabled = True
				else:
					print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', skipping entry'
					continue

				# Guess allowedtime
				elements = timer.getElementsByTagName("timespan")
				Len = len(elements)
				if Len:
					# Read out last definition
					start = elements[Len-1].getAttribute("from")
					end = elements[Len-1].getAttribute("to")
					if start and end:
						start = [int(x) for x in start.split(':')]
						end = [int(x) for x in end.split(':')]
						timetuple = (start, end)
					else:
						print '[AutoTimer] Erroneous config contains invalid definition of "timespan", ignoring definition'
						timetuple = None
				else:
					timetuple = None

				# Read out allowed services
				elements = timer.getElementsByTagName("serviceref")
				if len(elements):
					servicelist = []
					for service in elements:
						value = getValue(service, None, False)
						if value:
							servicelist.append(value)
				else:
					servicelist = None

				# Read out offset
				elements = timer.getElementsByTagName("offset")
				Len = len(elements)
				if Len:
					value = elements[Len-1].getAttribute("both")
					if value == '':
						before = int(elements[Len-1].getAttribute("before") or 0) * 60
						after = int(elements[Len-1].getAttribute("after") or 0) * 60
					else:
						before = after = int(value) * 60
					offset = (before, after)
				else:
					offset = None

				# Read out afterevent
				elements = timer.getElementsByTagName("afterevent")
				Len = len(elements)
				if Len:
					idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
					value = getValue(elements[Len-1], None, False)
					try:
						value = idx[value]
						start = elements[Len-1].getAttribute("from")
						end = elements[Len-1].getAttribute("to")
						if start and end:
							start = [int(x) for x in start.split(':')]
							end = [int(x) for x in end.split(':')]
							afterevent = (value, (start, end))
						else:
							afterevent = (value, None)
					except KeyError, ke:
						print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
						afterevent = None
				else:
					afterevent = None

				# Read out exclude
				elements = timer.getElementsByTagName("exclude")
				if len(elements):
					excludes = ([], [], [], [])
					idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
					for exclude in elements:
						where = exclude.getAttribute("where")
						value = getValue(exclude, None, False)
						if not (value and where):
							continue

						try:
							excludes[idx[where]].append(value.encode("UTF-8"))
						except KeyError, ke:
							pass
				else:
					excludes = None

				# Read out max length
				elements = timer.getElementsByTagName("maxduration")
				if len(elements):
					maxlen = getValue(elements, None)
					if maxlen is not None:
						maxlen = int(maxlen)*60
				else:
					maxlen = None

				# Finally append tuple
				self.timers.append(AutoTimerComponent(
						self.uniqueTimerId,
						name.encode('UTF-8'),
						enabled,
						timespan = timetuple,
						services = servicelist,
						offset = offset,
						afterevent = afterevent,
						exclude = excludes,
						maxduration = maxlen
				))

	def getTimerList(self):
		return self.timers

	def getEnabledTimerList(self):
		return [x for x in self.timers if x.enabled]

	def getTupleTimerList(self):
		return [(x,) for x in self.timers]

	def getUniqueId(self):
		self.uniqueTimerId += 1
		return self.uniqueTimerId

	def set(self, tuple):
		idx = 0
		for timer in self.timers:
			if timer.id == tuple.id:
				self.timers[idx] = tuple
				return
			idx += 1
		self.timers.append(tuple)

	def remove(self, uniqueId):
		idx = 0
		for timer in self.timers:
			if timer.id == uniqueId:
				self.timers.pop(idx)
				return
			idx += 1

	def writeXml(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<autotimer version="', CURRENT_CONFIG_VERSION, '">\n\n']

		# Iterate timers
		for timer in self.timers:
			list.extend([' <timer name="', timer.name, '" enabled="', timer.getEnabled(), '">\n'])
			if timer.hasTimespan():
				list.extend(['  <timespan from="', timer.getTimespanBegin(), '" to="', timer.getTimespanEnd(), '" />\n'])
			for serviceref in timer.getServices():
				list.extend(['  <serviceref>', serviceref, '</serviceref>\n'])
			if timer.hasOffset():
				if timer.isOffsetEqual():
					list.extend(['  <offset both="', str(timer.getOffsetBegin()), '" />\n'])
				else:
					list.extend(['  <offset before="', str(timer.getOffsetBegin()), '" after="', str(timer.getOffsetEnd()), '" />\n'])
			if timer.hasAfterEvent():
				afterevent = {AFTEREVENT.NONE: "none", AFTEREVENT.STANDBY: "standby", AFTEREVENT.DEEPSTANDBY: "shutdown"}[timer.getAfterEvent()]
				if timer.hasAfterEventTimespan():
					list.extend(['  <afterevent from="', timer.getAfterEventBegin(), '" to="', timer.getAfterEventEnd(), '">', afterevent, '</afterevent>\n'])
				else:
					list.extend(['  <afterevent>', afterevent, '</afterevent>\n'])
			for title in timer.getExcludedTitle():
				list.extend(['  <exclude where="title">', title, '</exclude>\n'])
			for short in timer.getExcludedShort():
				list.extend(['  <exclude where="shortdescription">', short, '</exclude>\n'])
			for desc in timer.getExcludedDescription():
				list.extend(['  <exclude where="description">', desc, '</exclude>\n'])
			for day in timer.getExcludedDays():
				list.extend(['  <exclude where="dayofweek>', day, '</exclude>\n'])
			if timer.hasDuration():
				list.extend(['  <maxduration>', str(timer.getDuration()), '</maxduration>\n'])
			list.append(' </timer>\n\n')
		list.append('</autotimer>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_CONFIG, 'w')
			file.writelines(list)

			# FIXME: This should actually be placed inside a finally-block but python 2.4 does not support this - waiting for some images to upgrade
			file.close()
			self.configMtime = time()
		except Exception, e:
			print "[AutoTimer] Error Saving Timer List:", e

	def parseEPG(self):
		new = 0
		skipped = 0

		# Get Configs mtime
		try:
			mtime = os_path.getmtime(XML_CONFIG)
		except:
			mtime = 0

		# Reparse Xml when needed
		if mtime != self.configMtime:
			self.readXml(mtime)

		# Iterate Timer
		for timer in self.getEnabledTimerList():
			try:
				# Search EPG
				ret = self.epgcache.search(('RI', 100, eEPGCache.PARTIAL_TITLE_SEARCH, timer.name, eEPGCache.NO_CASE_CHECK))

				# Continue on empty result
				if ret is None:
					print "[AutoTimer] Got empty result"
					continue

				for event in ret:
					# Format is (ServiceRef, EventId)
					# Example: ('1:0:1:445D:453:1:C00000:0:0:0:', 25971L)
					# Other information will be gathered from the Event
					print "[AutoTimer] Checking Tuple:", event

					# Check if Service is disallowed first as its the only property available here
					if timer.checkServices(event[0]):
						continue

					evt = self.epgcache.lookupEventId(eServiceReference(event[0]), event[1])
					if not evt:
						print "[AutoTimer] Could not create Event!"
						continue

					(begin, end, name, description, _) = parseEvent(evt)

					# If event starts in less than 60 seconds skip it
					if begin < time() + 60:
						continue

					# Convert begin time
					timestamp = localtime(begin)

					# Check Duration, Timespan and Excludes
					if timer.checkDuration(begin-end) or timer.checkTimespan(timestamp) or timer.checkExcluded(name, description, evt.getExtendedDescription(), str(timestamp[6])):
						continue

					# Check for double Timers
					unique = True
					for rtimer in self.session.nav.RecordTimer.timer_list:
						# Serviceref equals and eventId is the same
						if str(rtimer.service_ref) == event[0] and rtimer.eit == event[1]:
							print "[AutoTimer] Event already scheduled."
							unique = False
							skipped += 1
							break

					# If timer is "unique"
					if unique:
						print "[AutoTimer] Adding this event."
 
 						# Apply afterEvent
 						kwargs = {}
 						if timer.hasAfterEvent():
 							if timer.hasAfterEventTimespan():
 								if timer.checkAfterEventTimespan(localtime(end)):
 									kwargs["afterEvent"] = timer.getAfterEvent()
 							else:
 								kwargs["afterEvent"] = timer.getAfterEvent()
 
						# Apply custom offset
						begin, end = timer.applyOffset(begin, end)

						newEntry = RecordTimerEntry(ServiceReference(event[0]), begin, end, name, description, event[1], **kwargs)
						self.session.nav.RecordTimer.record(newEntry)
						new += 1

			except StandardError, se:
				# Give some more useful information
				import traceback, sys
				traceback.print_exc(file=sys.stdout)

		return (new, skipped)