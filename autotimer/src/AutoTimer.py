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

XML_CONFIG = "/etc/enigma2/autotimer.xml"

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
	if not len(ret.strip()):
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
			# Iterate Timers
			for timer in config.getElementsByTagName("timer"):
				# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None, timeoffset in m (before, after) or None, afterevent)

				# Increment uniqueTimerId
				self.uniqueTimerId += 1

				# Read out name
				name = getValue(timer.getElementsByTagName("name"), None)
				if name is None:
					print "[AutoTimer] Erroneous config, skipping entry"
					continue

				# Guess allowedtime
				elements = timer.getElementsByTagName("timespan")
				if len(elements):
					# We only support 1 Timespan so far
					start = getValue(elements[0].getElementsByTagName("from"), None)
					end = getValue(elements[0].getElementsByTagName("to"), None)
					if start and end:
						start = [int(x) for x in start.split(':')]
						end = [int(x) for x in end.split(':')]
						if end[0] < start[0] or (end[0] == start[0] and end[1] <= start[1]):
							haveDayspan = True
						else:
							haveDayspan = False
						timetuple = (start, end, haveDayspan)
					else:
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
					if not len(servicelist):
						servicelist = None
				else:
					servicelist = None

				# Read out offset
				elements = timer.getElementsByTagName("offset")
				if len(elements):
					value = getValue(elements[0], None, False)
					if value is None:
						before = int(getValue(elements[0].getElementsByTagName("before"), 0)) * 60
						after = int(getValue(elements[0].getElementsByTagName("after"), 0)) * 60
					else:
						before = after = int(value) * 60
					offset = (before, after)
				else:
					offset = None

				# Read out afterevent
				idx = {"standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
				afterevent = getValue(timer.getElementsByTagName("afterevent"), None)
				try:
					afterevent = idx[afterevent]
				except KeyError, ke:
					afterevent = AFTEREVENT.NONE					

				# Read out exclude
				elements = timer.getElementsByTagName("exclude")
				if len(elements):
					excludes = ([], [], [])
					idx = {"title": 0, "shortdescription": 1, "description": 2}
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
					maxlen = getValue(elements, None, False)
					if maxlen is not None:
						maxlen *= 60
				else:
					maxlen = None

				# Finally append tuple
				self.timers.append((
						self.uniqueTimerId,
						name.encode('UTF-8'),
						timetuple,
						servicelist,
						offset,
						afterevent,
						excludes,
						maxlen
				))

	def getTimerList(self):
		return self.timers

	def getUniqueId(self):
		self.uniqueTimerId += 1
		return self.uniqueTimerId

	def set(self, tuple):
		idx = 0
		for timer in self.timers:
			if timer[0] == tuple[0]:
				self.timers[idx] = tuple
				return
			idx += 1
		self.timers.append(tuple)

	def remove(self, uniqueId):
		idx = 0
		for timer in self.timers:
			if timer[0] == uniqueId:
				self.timers.pop(idx)
				return

	def writeXml(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<autotimer>\n\n']

		# Iterate timers
		for timer in self.timers:
			list.append(' <timer>\n')
			list.append(''.join(['  <name>', timer[1], '</name>\n']))
			if timer[2] is not None:
				list.append('  <timespan>\n')
				list.append(''.join(['   <from>', '%02d:%02d' % (timer[2][0][0], timer[2][0][1]), '</from>\n']))
				list.append(''.join(['   <to>', '%02d:%02d' % (timer[2][1][0], timer[2][1][1]), '</to>\n']))
				list.append('  </timespan>\n')
			if timer[3] is not None:
				for serviceref in timer[3]:
					list.append(''.join(['  <serviceref>', serviceref, '</serviceref>\n']))
			if timer[4] is not None:
				if timer[4][0] == timer[4][1]:
					list.append(''.join(['  <offset>', str(timer[4][0]/60), '</offset>\n']))
				else:
					list.append('  <offset>\n')
					list.append(''.join(['   <before>', str(timer[4][0]/60), '</before>\n']))
					list.append(''.join(['   <after>', str(timer[4][1]/60), '</after>\n']))
					list.append('  </offset>\n')
			if timer[5] is not AFTEREVENT.NONE:
				afterevent = {AFTEREVENT.STANDBY: "standby", AFTEREVENT.DEEPSTANDBY: "shutdown"}[timer[5]]
				list.append(''.join(['  <afterevent>', afterevent, '</afterevent>\n']))
			if timer[6] is not None:
				for title in timer[6][0]:
					list.append(''.join(['  <exclude where="title">', title, '</exclude>\n']))
				for short in timer[6][1]:
					list.append(''.join(['  <exclude where="shortdescription">', short, '</exclude>\n']))
				for desc in timer[6][2]:
					list.append(''.join(['  <exclude where="description">', desc, '</exclude>\n']))
			if timer[7] is not None:
				list.append(''.join(['  <maxduration>', str(timer[7]/60), '</maxduration>\n']))
			list.append(' </timer>\n\n')
		list.append('</autotimer>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_CONFIG, "w")
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
		for timer in self.timers:
			try:
				# Search EPG
				ret = self.epgcache.search(('RI', 100, eEPGCache.PARTIAL_TITLE_SEARCH, timer[1], eEPGCache.NO_CASE_CHECK))

				# Continue on empty result
				if ret is None:
					print "[AutoTimer] Got empty result"
					continue

				for event in ret:
					# Format is (ServiceRef, EventId)
					# Example: ('1:0:1:445D:453:1:C00000:0:0:0:', 25971L)
					# Other information will be gathered from the Event
					print "[AutoTimer] Checking Tuple:", event
					
					ref = eServiceReference(event[0])
					evt = self.epgcache.lookupEventId(ref, event[1])
					if not evt:
						print "[AutoTimer] Could not create Event!"
						continue

					(begin, end, name, description, _) = parseEvent(evt)

					# If event starts in less than 60 seconds skip it
					if begin < time() + 60:
						continue

					# Check if duration exceeds our limit
					if timer[7] is not None:
						if begin-end > timer[7]:
							continue

					# Check if we have Timelimit
					if timer[2] is not None:
						# Calculate Span if needed

						# TODO: We don't want to check the whole event but only its start...
						# so we might aswell just check the clock rather than the day

						if timer[2][2]:
							# Make List of yesterday & today
							yesterday = [x for x in localtime(begin - 86400)]
							today = [x for x in localtime(begin)]

							# Make yesterday refer to yesterday's begin of timespan
							yesterday[3] = timer[2][0][0]
							yesterday[4] = timer[2][0][1]

							# Make today refer to this days end of timespan
							today[3] = timer[2][1][0]
							today[4] = timer[2][1][1]
							
							# Convert back
							begin = mktime(yesterday)
							end = mktime(today)

							# Check if Event starts between eventday and the day before
							if (begin > begin or end < begin):
								# Make List of tomorrow
								tomorrow = [x for x in localtime(begin + 86400)]

								# Today -> begin of timespan
								today[3] = timer[2][0][0]
								today[4] = timer[2][0][1]

								# Tomorrow -> end of timespan
								tomorrow[3] = timer[2][1][0]
								tomorrow[4] = timer[2][1][1]
							
								# Convert back
								begin = mktime(today)
								end = mktime(tomorrow)

								# Check if Event starts between eventday and day after
								if begin > begin or end < begin:
									continue
						else:
							# Make List
							today = [x for x in localtime(begin)]

							# Modify List to refer to begin of timespan
							today[3] = timer[2][0][0]
							today[4] = timer[2][0][1]

							# Convert List back to timetamp
							begin = mktime(today)

							# Same for end of timespan
							today[3] = timer[2][1][0]
							today[4] = timer[2][1][1]
							end = mktime(today)

							# Check if event starts between timespan
							if begin > begin or end < begin:
								continue

					# Check if we have Servicelimit
					if timer[3] is not None:
						# Continue if service not allowed
						if event[0] not in timer[3]:
							continue

					# Check if we have excludes
					if timer[6] is not None:
						ext_desc = evt.getExtendedDescription()
						stop = False
						# Continue if exclude found in string
						for title in timer[6][0]:
							if title in name:
								stop = True
								break
						if stop:
							continue
						for short in timer[6][1]:
							if short in description:
								stop = True
								break
						if stop:
							continue
						for desc in timer[6][2]:
							if desc in ext_desc:
								stop = True
								break
						if stop:
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
 
						# Apply custom offset
						if timer[4] is not None:
							begin -= timer[4][0]
							end += timer[4][1]

						newEntry = RecordTimerEntry(ServiceReference(event[0]), begin, end, name, description, event[1], afterEvent = timer[5])
						self.session.nav.RecordTimer.record(newEntry)
						new += 1

			except StandardError, se:
				# Give some more useful information
				import traceback, sys
				traceback.print_exc(file=sys.stdout)

		return (new, skipped)