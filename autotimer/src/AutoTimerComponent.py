# Needed to check timespans
from time import localtime

class AutoTimerComponent(object):
	def __init__(self, id, *args, **kwargs):
		self.id = id
		self.setValues(*args, **kwargs)

	def setValues(self, name, enabled, timespan = None, services = None, offset = None, afterevent = None, exclude = None, maxduration = None):
		self.name = name
		self.timespan = timespan
		self.services = services
		self.offset = offset
		self.afterevent = afterevent
		self.exclude = exclude
		self.maxduration = maxduration
		self.enabled = enabled

	def calculateDayspan(self, timespan):
		if timespan and (timespan[1][0] < timespan[0][0] or (timespan[1][0] == timespan[0][0] and timespan[1][1] <= timespan[0][1])):
			return (timespan, True)
		else:
			return (timespan, False)

	def setTimespan(self, timespan):
		self._timespan = self.calculateDayspan(timespan)

	def getTimespan(self):
		return self._timespan

	timespan = property(getTimespan, setTimespan)

	def setExclude(self, exclude):
		if exclude and (len(self.excludes[0]) or len(self.excludes[1]) or len(self.excludes[2])):
			self._exclude = exclude
		else:
			self._exclude = None

	def getExclude(self):
		return self._exclude

	exclude = property(getExclude, setExclude)

	def setServices(self, services):
		if services and len(services):
			self._services = services
		else:
			self._services = None

	def getServices(self):
		return self._services

	services = property(getServices, setServices)

	def setAfterEvent(self, afterevent):
		if afterevent is None:
			self._afterevent = None
		else:
			afterevent, timespan = afterevent
			self._afterevent = (afterevent, self.calculateDayspan(timespan))

	def getCompleteAfterEvent(self):
		return self._afterevent

	afterevent = property(getCompleteAfterEvent, setAfterEvent)

	def hasTimespan(self):
		return self.timespan[0] is not None

	def getTimespanBegin(self):
		return '%02d:%02d' % (self.timespan[0][0][0], self.timespan[0][0][1])

	def getTimespanEnd(self):
		return '%02d:%02d' % (self.timespan[0][1][0], self.timespan[0][1][1])

	def checkAnyTimespan(self, timestamp, span, haveDayspan):
		if span is None:
			return False

		# Calculate Span if needed
		time = localtime(timestamp) # 3 is h, 4 is m

		# Check if we span a day
		if haveDayspan:
			# Check if begin of event is later than our timespan starts
			if time[3] > span[0][0] or (time[3] == span[0][0] and time[4] >= span[0][1]):
				# If so, event is in our timespan
				return True
			# If it does check if it is earlier than out timespan ends
			if time[3] < span[1][0] or (time[3] == span[1][0] and time[4] <= span[1][1]):
				# If so, event is in our timespan
				return True
			return False
		else:
			# Check if event begins earlier than our timespan starts 
			if time[3] < span[0][0] or (time[3] == span[0][0] and time[4] <= span[0][1]):
				# Its out of our timespan then
				return True
			# Check if event begins later than out timespan ends
			if time[3] > span[1][0] or (time[3] == span[1][0] and time[4] >= span[1][1]):
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

	def getServices(self):
		if self.services is None:
			return []
		return self.services

	def checkServices(self, service):
		if self.services is None:
			return False
		return service not in self.services

	def getExcludedTitle(self):
		if self.exclude is None:
			return []
		return self.exclude[0]

	def getExcludedShort(self):
		if self.exclude is None:
			return []
		return self.exclude[1]

	def getExcludedDescription(self):
		if self.exclude is None:
			return []
		return self.exclude[2]

	def checkExcluded(self, title, short, extended):
		if self.exclude is None:
			return False

		for exclude in self.excludes[0]:
			if exclude in title:
				return True
		for exclude in self.excludes[1]:
			if exclude in short:
				return True
		for exclude in self.excludes[2]:
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
		return self.afterevent is not None

	def hasAfterEventTimespan(self):
		return self.afterevent[1][0] is not None

	def checkAfterEventTimespan(self, end):
		return self.checkAnyTimespan(end, *self.afterevent[1])

	def getAfterEvent(self):
		return self.afterevent[0]

	def getAfterEventBegin(self):
		return '%02d:%02d' % (self.afterevent[1][0][0][0], self.afterevent[1][0][0][1])

	def getAfterEventEnd(self):
		return '%02d:%02d' % (self.afterevent[1][0][1][0], self.afterevent[1][0][1][1])

	def getEnabled(self):
		return self.enabled and "yes" or "no"

	def __repr__(self):
		return "<AutomaticTimer " + self.name + " (" + str(self.timespan) + ", " + str(self.services) + ", " + str(self.offset) + ", " + str(self.afterevent) + ", " + str(self.exclude) + ", " + str(self.maxduration) + ", " + str(self.enabled) + ")>"
