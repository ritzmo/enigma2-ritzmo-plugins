# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, ConfigYesNo, ConfigText, ConfigClock, ConfigInteger, ConfigSelection

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

class AutoTimerEditor(Screen, ConfigListScreen):
	"""Edit AutoTimer"""

	skin = """<screen name="AutoTimerEdit" title="Edit AutoTimer" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timer):
		Screen.__init__(self, session)

		# Keep Timer
		self.timer = timer

		# Summary
		self.setup_title = "AutoTimer Editor"
		self.onChangedEntry = []

		# See if we are excluding some strings
		self.excludes = (timer.getExcludedTitle(), timer.getExcludedShort(), timer.getExcludedDescription(), timer.getExcludedDays())
		if len(self.excludes[0]) or len(self.excludes[1]) or len(self.excludes[2]) or len(self.excludes[3]):
			self.excludesSet = True
		else:
			self.excludesSet = False

		# See if services are restricted
		self.services = timer.getServices()
		if len(self.services):
			self.serviceRestriction = True
		else:
			self.serviceRestriction = False

		self.createSetup(timer)

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.reloadList, initial_call = False)
		self.offset.addNotifier(self.reloadList, initial_call = False)
		self.duration.addNotifier(self.reloadList, initial_call = False)
		self.afterevent.addNotifier(self.reloadList, initial_call = False)
		self.afterevent_timespan.addNotifier(self.reloadList, initial_call = False)

		self.refresh()

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Edit Excludes"))
 		self["key_blue"] = Button(_("Edit Channels"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.maybeSave,
				"yellow": self.editExcludes,
				"blue": self.editChannels
			}
		)

		# Trigger change
		self.changed()

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def createSetup(self, timer):
		# Name
		self.name = ConfigText(default = timer.name, fixed_size = False)

		# Match
		self.match = ConfigText(default = timer.match, fixed_size = False)

		# Timespan
		now = [x for x in localtime()]
		if timer.hasTimespan():
			default = True
			now[3] = timer.timespan[0][0]
			now[4] = timer.timespan[0][1]
			begin = mktime(now)
			now[3] = timer.timespan[1][0]
			now[4] = timer.timespan[1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 20
			now[4] = 15
			begin = mktime(now)
			now[3] = 23
			now[4] = 15
			end = mktime(now)
		self.timespan = ConfigEnableDisable(default = default)
		self.timespanbegin = ConfigClock(default = begin)
		self.timespanend = ConfigClock(default = end)

		# Services have their own Screen

		# Offset
		if timer.hasOffset():
			default = True
			begin = timer.getOffsetBegin()
			end = timer.getOffsetEnd()
		else:
			default = False
			begin = 5
			end = 5
		self.offset = ConfigEnableDisable(default = default)
		self.offsetbegin = ConfigInteger(default = begin, limits = (0, 60))
		self.offsetend = ConfigInteger(default = end, limits = (0, 60))

		# AfterEvent
		if timer.hasAfterEvent():
			afterevent = { None: "default", AFTEREVENT.NONE: "nothing", AFTEREVENT.DEEPSTANDBY: "deepstandby", AFTEREVENT.STANDBY: "standby"}[timer.afterevent[0][0]]
		else:
			afterevent = "default"
		self.afterevent = ConfigSelection(choices = [("default", _("standard")), ("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby"))], default = afterevent)

		# AfterEvent (Timespan)
		if timer.hasAfterEvent() and timer.afterevent[0][1][0] is not None:
			default = True
			now[3] = timer.afterevent[1][0][0][0]
			now[4] = timer.afterevent[1][0][0][1]
			begin = mktime(now)
			now[3] = timer.afterevent[1][1][1][0]
			now[4] = timer.afterevent[1][1][1][1]
			end = mktime(now)
		else:
			default = False
			now[3] = 23
			now[4] = 15
			begin = mktime(now)
			now[3] = 7
			now[4] = 0
			end = mktime(now)
		self.afterevent_timespan = ConfigEnableDisable(default = default)
		self.afterevent_timespanbegin = ConfigClock(default = begin)
		self.afterevent_timespanend = ConfigClock(default = end)

		# Enabled
		self.enabled = ConfigYesNo(default = timer.enabled)

		# Maxduration
		if timer.hasDuration():
			default = True
			duration = timer.getDuration()
		else:
			default = False
			duration =70
		self.duration = ConfigEnableDisable(default = default)
		self.durationlength = ConfigInteger(default = duration, limits = (0, 600))

	def refresh(self):
		# First four entries are always shown
		self.list = [
			getConfigListEntry(_("Enabled"), self.enabled),
			getConfigListEntry(_("Description"), self.name),
			getConfigListEntry(_("Match Title"), self.match),
			getConfigListEntry(_("Only match during Timespan"), self.timespan)
		]

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.list.extend([
				getConfigListEntry(_("Begin of Timespan"), self.timespanbegin),
				getConfigListEntry(_("End of Timespan"), self.timespanend)
			])

		self.list.append(getConfigListEntry(_("Custom offset"), self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			self.list.extend([
				getConfigListEntry(_("Offset before recording (in m)"), self.offsetbegin),
				getConfigListEntry(_("Offset after recording (in m)"), self.offsetend)
			])

		self.list.append(getConfigListEntry(_("Set maximum Duration"), self.duration))

		# Only allow editing maxduration when it's enabled
		if self.duration.value:
			self.list.extend([
				getConfigListEntry(_("Maximum Duration (in m)"), self.durationlength)
			])

		self.list.append(getConfigListEntry(_("After event"), self.afterevent))

		# Only allow setting afterevent timespan when afterevent is active
		if self.afterevent.value != "default":
			self.list.append(getConfigListEntry(_("Execute after Event during Timespan"), self.afterevent_timespan))

			# Only allow editing timespan when it's enabled
			if self.afterevent_timespan.value:
				self.list.extend([
					getConfigListEntry(_("Begin of after Event Timespan"), self.afterevent_timespanbegin),
					getConfigListEntry(_("End of after Event Timespan"), self.afterevent_timespanend)
				])

	def reloadList(self, value):
		self.refresh()
		self["config"].setList(self.list)

	def editExcludes(self):
		self.session.openWithCallback(
			self.editExcludesCallback,
			AutoTimerExcludeEditor,
			self.excludesSet,
			self.excludes
		)

	def editExcludesCallback(self, ret):
		if ret:
			self.excludesSet = ret[0]
			self.excludes = ret[1]

	def editChannels(self):
		self.session.openWithCallback(
			self.editChannelsCallback,
			AutoTimerChannelEditor,
			self.serviceRestriction,
			self.services
		)

	def editChannelsCallback(self, ret):
		if ret:
			self.serviceRestriction = ret[0]
			self.services = ret[1] 

	def cancel(self):
		self.close(None)

	def maybeSave(self):
		# Check if we have a trailing whitespace
		if self.match.value[-1:] == " ":
			self.session.openWithCallback(
				self.saveCallback,
				MessageBox,
				_('You entered "%s" as Text to match.\nDo you want to remove trailing whitespaces?') % (self.match.value)
			)
		# Just save else
		else:
			self.save()

	def saveCallback(self, ret):
		if ret is not None:
			if ret:
				self.match.value = self.match.value.rstrip()
			self.save()
		# Don't to anything if MessageBox was canceled!

	def save(self):
		# Match
		self.timer.match = self.match.value

		# Name
		self.timer.name = self.name.value or self.timer.match

		# Enabled
		self.timer.enabled = self.enabled.value

		# Timespan
		if self.timespan.value:
			start = self.timespanbegin.value
			end = self.timespanend.value
			self.timer.timespan = (start, end)
		else:
			self.timer.timespan = None

		# Services
		if self.serviceRestriction:
			self.timer.services = self.services
		else:
			self.timer.services = None

		# Offset
		if self.offset.value:
			self.timer.offset = (self.offsetbegin.value*60, self.offsetend.value*60)
		else:
			self.timer.offset = None

		# AfterEvent
		if self.afterevent.value == "default":
			self.timer.afterevent = []
		else:
			afterevent = {"nothing": AFTEREVENT.NONE, "deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY}[self.afterevent.value]
			# AfterEvent Timespan
			if self.afterevent_timespan.value:
				start = self.afterevent_timespanbegin.value
				end = self.afterevent_timespanend.value
				self.timer.afterevent = [(afterevent, (start, end))]
			else:
				self.timer.afterevent = [(afterevent, None)]

		# Maxduration
		if self.duration.value:
			self.timer.maxduration = self.durationlength.value*60
		else:
			self.timer.maxduration = None

		# Excludes
		if self.excludesSet:
			self.timer.exclude = self.excludes
		else:
			self.timer.exclude = None

		# Close
		self.close(self.timer)

class AutoTimerExcludeEditor(Screen, ConfigListScreen):
	"""Edit AutoTimer Excludes"""

	skin = """<screen name="AutoExcludeEdit" title="Edit AutoTimer Excludes" position="75,150" size="565,245">
		<widget name="config" position="5,5" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap position="5,205" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,205" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,205" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,205" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, excludeset, excludes):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "AutoTimer Excludes"
		self.onChangedEntry = []

		self.list = [
			getConfigListEntry(_("Enable Filtering"), ConfigEnableDisable(default = excludeset))
		]

		self.list.extend([
			getConfigListEntry(_("Filter in Title"), ConfigText(default = x, fixed_size = False))
				for x in excludes[0]
		])
		self.lenTitles = len(self.list)
		self.list.extend([
			getConfigListEntry(_("Filter in Shortdescription"), ConfigText(default = x, fixed_size = False))
				for x in excludes[1]
		])
		self.lenShorts = len(self.list)
		self.list.extend([
			getConfigListEntry(_("Filter in Description"), ConfigText(default = x, fixed_size = False))
				for x in excludes[2]
		])
		self.lenDescs = len(self.list)
		weekdays = [("0", _("Monday")), ("1", _("Tuesday")),  ("2", _("Wednesday")),  ("3", _("Thursday")),  ("4", _("Friday")),  ("5", _("Saturday")),  ("6", _("Sunday")), ("weekend", _("Weekend"))]
		self.list.extend([
			getConfigListEntry(_("Filter on Weekday"), ConfigSelection(choices = weekdays, default = x))
				for x in excludes[3]
		])

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.remove,
				"blue": self.new
			}
		)

		# Trigger change
		self.changed()

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def remove(self):
		idx = self["config"].getCurrentIndex()
		if idx:
			if idx < self.lenTitles:
				self.lenTitles -= 1
				self.lenShorts -= 1
				self.lenDescs -= 1
			elif idx < self.lenShorts:
				self.lenShorts -= 1
				self.lenDescs -= 1
			elif idx < self.lenDescs:
				self.lenDescs -= 1

			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)

	def new(self):
		self.session.openWithCallback(
			self.typeSelected,
			ChoiceBox,
			_("Select type of Filter"),
			[
				(_("Title"), 0),
				(_("Shortdescription"), 1),
				(_("Description"), 2),
				(_("Weekday"), 3)
			]
			
		)

	def typeSelected(self, ret):
		if ret is not None:
			list = self["config"].getList()

			if ret[1] == 0:
				pos = self.lenTitles
				self.lenTitles += 1
				self.lenShorts += 1
				self.lenDescs += 1
				entry = getConfigListEntry(_("Filter in Title"), ConfigText(fixed_size = False))
			elif ret[1] == 1:
				pos = self.lenShorts
				self.lenShorts += 1
				self.lenDescs += 1
				entry = getConfigListEntry(_("Filter in Shortdescription"), ConfigText(fixed_size = False))
			elif ret[1] == 2:
				pos = self.lenDescs
				self.lenDescs += 1
				entry = getConfigListEntry(_("Filter in Description"), ConfigText(fixed_size = False))
			else:
				pos = len(self.list)
				weekdays = [("0", _("Monday")), ("1", _("Tuesday")),  ("2", _("Wednesday")),  ("3", _("Thursday")),  ("4", _("Friday")),  ("5", _("Saturday")),  ("6", _("Sunday")), ("weekend", _("Weekend"))]
				entry = getConfigListEntry(_("Filter on Weekday"), ConfigSelection(choices = weekdays))

			list.insert(pos, entry)
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		list = self["config"].getList()
		restriction = list.pop(0)

		# Warning, accessing a ConfigListEntry directly might be considered evil!

		idx = 0
		excludes = ([], [], [], [])
		for item in list:
			# Increment Index
			idx += 1

			# Skip empty entries
			if item[1].value == "":
				continue
			elif idx < self.lenTitles:
				excludes[0].append(item[1].value.encode("UTF-8"))
			elif idx < self.lenShorts:
				excludes[1].append(item[1].value.encode("UTF-8"))
			elif idx < self.lenDescs:
				excludes[2].append(item[1].value.encode("UTF-8"))
			else:
				excludes[3].append(item[1].value)

		self.close((
			restriction[1].value,
			excludes
		))

class AutoTimerChannelEditor(Screen, ConfigListScreen):
	"""Edit allowed Channels of a AutoTimer"""

	skin = """<screen name="AutoChannelEdit" title="Edit AutoTimer Channels" position="75,150" size="565,245">
		<widget name="config" position="5,5" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap position="5,205" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,205" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,205" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,205" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,205" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, servicerestriction, servicelist):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "AutoTimer Channels"
		self.onChangedEntry = []

		self.list = [
			getConfigListEntry(_("Enable Channel Restriction"), ConfigEnableDisable(default = servicerestriction))
		]

		self.list.extend([
			getConfigListEntry(_("Record on"), ConfigSelection(choices = [(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))]))
				for x in servicelist
		])

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.removeChannel,
				"blue": self.newChannel
			}
		)

		# Trigger change
		self.changed()

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def removeChannel(self):
		if self["config"].getCurrentIndex() != 0:
			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)

	def newChannel(self):
		self.session.openWithCallback(
			self.finishedChannelSelection,
			SimpleChannelSelection,
			_("Select channel to record from")
		)

	def finishedChannelSelection(self, *args):
		if len(args):
			list = self["config"].getList()
			list.append(getConfigListEntry(_("Record on"), ConfigSelection(choices = [(args[0].toString(), ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''))])))
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		list = self["config"].getList()
		restriction = list.pop(0)

		# Warning, accessing a ConfigListEntry directly might be considered evil!
		self.close((
			restriction[1].value,
			[
				x[1].value.encode("UTF-8")
					for x in list
			]
		))
