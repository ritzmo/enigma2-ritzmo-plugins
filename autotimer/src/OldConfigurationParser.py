from AutoTimerComponent import AutoTimerComponent
from AutoTimer import getValue
from RecordTimer import AFTEREVENT

def parseConfig(configuration, list, version = None):
	print "[AutoTimer] Trying to parse old config file"
	parseConfig_v1(configuration, list)

def parseConfig_v1(configuration, list):
	uniqueTimerId = 0
	# Iterate Timers
	for timer in configuration.getElementsByTagName("timer"):
		# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None, timeoffset in m (before, after) or None, afterevent)

		# Increment uniqueTimerId
		uniqueTimerId += 1

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
				timetuple = (start, end)
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
		else:
			servicelist = None

		# Read out offset
		elements = timer.getElementsByTagName("offset")
		if len(elements):
			value = getValue(elements, None)
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
			afterevent = (idx[afterevent], None)
		except KeyError, ke:
			# TODO: do we really want to copy this behaviour?
			afterevent = (AFTEREVENT.NONE, None)

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
			maxlen = getValue(elements, None)
			if maxlen is not None:
				maxlen = int(maxlen)*60
		else:
			maxlen = None

		# Read out enabled status
		elements = timer.getElementsByTagName("enabled")
		if len(elements):
			if getValue(elements, "yes") == "no":
				enabled = False
			else:
				enabled = True
		else:
			enabled = True

		# Finally append tuple
		list.append(AutoTimerComponent(
				uniqueTimerId,
				name.encode('UTF-8'),
				enabled,
				timespan = timetuple,
				services = servicelist,
				offset = offset,
				afterevent = afterevent,
				exclude = excludes,
				maxduration = maxlen
		))