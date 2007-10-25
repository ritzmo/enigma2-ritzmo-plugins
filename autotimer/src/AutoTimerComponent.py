class AutoTimerComponent(object):
	"""AutoTimer Component which also handles validity checks"""

	def __init__(self, id, *args, **kwargs):
		self.id = id
		self._afterevent = []
		self.setValues(*args, **kwargs)

	def __eq__(self, other):
		try:
			return self.id == other.id
		except AttributeError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def setValues(self, name, match, enabled, timespan = None, services = None, offset = None, afterevent = [], exclude = None, maxduration = None, destination = None):
		self.name = name
		self.match = match
		self.timespan = timespan
		self.services = services
		self.offset = offset
		self.afterevent = afterevent
		self.exclude = exclude
		self.maxduration = maxduration
		self.enabled = enabled
		self.destination = destination

	def calculateDayspan(self, begin, end):
		if end[0] < begin[0] or (end[0] == begin[0] and end[1] <= begin[1]):
			return (begin, end, True)
		else:
			return (begin, end, False)

	def setTimespan(self, timespan):
		if timespan is None:
			self._timespan = (None,)
		else:
			self._timespan = self.calculateDayspan(*timespan)

	def getTimespan(self):
		return self._timespan

	timespan = property(getTimespan, setTimespan)

	def setExclude(self, exclude):
		if exclude and (len(exclude[0]) or len(exclude[1]) or len(exclude[2]) or len(exclude[3])):
			# Filter for virtual Weekdays
			days = []
			for x in exclude[3]:
				if x == "weekend":
					days.append(5)
					days.append(6)
				else:
					days.append(x)

			self._exclude = (exclude[0], exclude[1], exclude[2], days)
		else:
			self._exclude = None

	def getExclude(self):
		return self._exclude

	exclude = property(getExclude, setExclude)

	def setServices(self, services):
		if services:
			self._services = services
		else:
			self._services = []

	def getServices(self):
		return self._services

	services = property(getServices, setServices)

	def setAfterEvent(self, afterevent):
		del self._afterevent[:]
		if len(afterevent):
			for definition in afterevent:
				action, timespan = definition
				if timespan is None:
					self._afterevent.append((action, (None,)))
				else:
					self._afterevent.append((action, self.calculateDayspan(*timespan)))

	def getCompleteAfterEvent(self):
		return self._afterevent

	afterevent = property(getCompleteAfterEvent, setAfterEvent)

	def hasTimespan(self):
		return self.timespan[0] is not None

	def getTimespanBegin(self):
		return '%02d:%02d' % (self.timespan[0][0], self.timespan[0][1])

	def getTimespanEnd(self):
		return '%02d:%02d' % (self.timespan[1][0], self.timespan[1][1])

	def checkAnyTimespan(self, time, begin = None, end = None, haveDayspan = False):
		if begin is None:
			return False

		# Check if we span a day
		if haveDayspan:
			# Check if begin of event is later than our timespan starts
			if time[3] > begin[0] or (time[3] == begin[0] and time[4] >= begin[1]):
				# If so, event is in our timespan
				return False
			# Check if begin of event is earlier than our timespan end
			if time[3] < end[0] or (time[3] == end[0] and time[4] <= end[1]):
				# If so, event is in our timespan
				return False
			return True
		else:
			# Check if event begins earlier than our timespan starts 
			if time[3] < begin[0] or (time[3] == begin[0] and time[4] < begin[1]):
				# Its out of our timespan then
				return True
			# Check if event begins later than our timespan ends
			if time[3] > end[0] or (time[3] == end[0] and time[4] > end[1]):
				# Its out of our timespan then
				return True
			return False

	def checkTimespan(self, begin):
		return self.checkAnyTimespan(begin, *self.timespan)

	def hasDuration(self):
		return self.maxduration is not None

	def getDuration(self):
		return self.maxduration/60

	def checkDuration(self, length):
		if self.maxduration is None:
			return False
		return length > self.maxduration

	def checkServices(self, service):
		if not len(self.services):
			return False
		return service not in self.services

	def getExcludedElement(self, id):
		if self.exclude is None:
			return []
		return self.exclude[id]

	def getExcludedTitle(self):
		return self.getExcludedElement(0)

	def getExcludedShort(self):
		return self.getExcludedElement(1)

	def getExcludedDescription(self):
		return self.getExcludedElement(2)

	def getExcludedDays(self):
		list = self.getExcludedElement(3)
		if "5" in list and "6" in list:
			list.remove("5")
			list.remove("6")
			list.append("weekend")
		return list

	def checkExcluded(self, title, short, extended, dayofweek):
		if self.exclude is None:
			return False

		for exclude in self.exclude[3]:
			if exclude == dayofweek:
				return True
		for exclude in self.exclude[0]:
			if exclude in title:
				return True
		for exclude in self.exclude[1]:
			if exclude in short:
				return True
		for exclude in self.exclude[2]:
			if exclude in extended:
				return True
		return False

	def hasOffset(self):
		return self.offset is not None

	def isOffsetEqual(self):
		return self.offset[0] == self.offset[1]

	def applyOffset(self, begin, end):
		if self.offset is None:
			return (begin, end)
		return (begin - self.offset[0], end + self.offset[1])

	def getOffsetBegin(self):
		return self.offset[0]/60

	def getOffsetEnd(self):
		return self.offset[1]/60

	def hasAfterEvent(self):
		return len(self.afterevent)

	def hasAfterEventTimespan(self):
		for afterevent in self.afterevent:
			if afterevent[1][0] is not None:
				return True
		return False

	def getAfterEventTimespan(self, end):
		for afterevent in self.afterevent:
			if not self.checkAnyTimespan(end, *afterevent[1]):
				return afterevent[0]
		return None

	def getAfterEvent(self):
		for afterevent in self.afterevent:
			if afterevent[1][0] is None:
				return afterevent[0]
		return None

	def getEnabled(self):
		return self.enabled and "yes" or "no"

	def hasDestination(self):
		return self.destination is not None

	def __repr__(self):
		return ''.join([
			'<AutomaticTimer ',
			self.name,
			' (',
			', '.join([
					str(self.match),
			 		str(self.timespan),
			 		str(self.services),
			 		str(self.offset),
			 		str(self.afterevent),
			 		str(self.exclude),
			 		str(self.maxduration),
			 		str(self.enabled),
			 		str(self.destination)
			 ]),
			 ")>"
		])
