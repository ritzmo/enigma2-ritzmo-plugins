class AutoTimerComponent(object):
	"""AutoTimer Component which also handles validity checks"""

	def __init__(self, id, *args, **kwargs):
		self.id = id
		self.setValues(*args, **kwargs)

	def setValues(self, name, match, enabled, timespan = None, services = None, offset = None, afterevent = None, exclude = None, maxduration = None):
		self.name = name
		self.match = match
		self.timespan = timespan
		self.services = services
		self.offset = offset
		self.afterevent = afterevent
		self.exclude = exclude
		self.maxduration = maxduration
		self.enabled = enabled

	def calculateDayspan(self, begin, end):
		if end[0] < begin[0] or (end[0] == begin[0] and end[1] <= begin[1]):
			return (begin, end, True)
		else:
			return (begin, end, False)

	def setMatch(self, match):
		self._match = match.strip()

	def getMatch(self):
		return self._match

	match = property(getMatch, setMatch)

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
			self._exclude = exclude
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
		if afterevent is None:
			self._afterevent = (None, (None,))
		else:
			afterevent, timespan = afterevent
			if timespan is None:
				self._afterevent = (afterevent, (None,))
			else:
				self._afterevent = (afterevent, self.calculateDayspan(*timespan))

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
			if time[3] < begin[0] or (time[3] == begin[0] and time[4] <= begin[1]):
				# Its out of our timespan then
				return True
			# Check if event begins later than our timespan ends
			if time[3] > end[0] or (time[3] == end[0] and time[4] >= end[1]):
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
		if self.services is None:
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
		return self.getExcludedElement(3)

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
		return self.afterevent[0] is not None

	def hasAfterEventTimespan(self):
		return self.afterevent[1][0] is not None

	def checkAfterEventTimespan(self, end):
		return self.checkAnyTimespan(end, *self.afterevent[1])

	def getAfterEvent(self):
		return self.afterevent[0]

	def getAfterEventBegin(self):
		return '%02d:%02d' % (self.afterevent[1][0][0], self.afterevent[1][0][1])

	def getAfterEventEnd(self):
		return '%02d:%02d' % (self.afterevent[1][1][0], self.afterevent[1][1][1])

	def getEnabled(self):
		return self.enabled and "yes" or "no"

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
			 		str(self.enabled)
			 ]),
			 ")>"
		])
