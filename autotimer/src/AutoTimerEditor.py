# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from AutoTimerChannelEditor import AutoTimerChannelEditor
from AutoTimerExcludeEditor import AutoTimerExcludeEditor

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, ConfigYesNo, ConfigText, ConfigClock, ConfigInteger, ConfigSelection

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

class AutoTimerEditor(Screen, ConfigListScreen):
	skin = """<screen name="AutoTimerEdit" title="Edit AutoTimer" position="75,130" size="565,325">
		<widget name="config" position="5,5" size="555,280" scrollbarMode="showOnDemand" />
		<ePixmap position="0,285" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,285" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,285" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,285" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,285" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,285" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,285" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,285" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timer):
		Screen.__init__(self, session)

		# Keep Timer
		self.timer = timer

		# See if we are excluding some strings
		self.excludes = (timer.getExcludedTitle(), timer.getExcludedShort(), timer.getExcludedDescription())
		if len(self.excludes[0]) or len(self.excludes[1]) or len(self.excludes[2]):
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

		self.refresh()

		ConfigListScreen.__init__(self, self.list, session = session)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Edit Excludes"))
 		self["key_blue"] = Button(_("Edit Channels"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.editExcludes,
				"blue": self.editChannels
			}
		)

	def createSetup(self, timer):
		# Name
		self.name = ConfigText(default = timer.name, fixed_size = False)

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
		afterevent = { AFTEREVENT.NONE: "nothing", AFTEREVENT.DEEPSTANDBY: "deepstandby", AFTEREVENT.STANDBY: "standby"}[timer.getAfterEvent()]
		self.afterevent = ConfigSelection(choices = [("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby"))], default = afterevent)

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
		# First two entries are always shown
		self.list = [
			getConfigListEntry(_("Enabled"), self.enabled),
			getConfigListEntry(_("Match Title"), self.name),
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
		self.close()

	def save(self):
		# Name
		self.timer.name = self.name.value

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
		self.timer.afterevent = {"nothing": AFTEREVENT.NONE, "deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY}[self.afterevent.value]

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
		self.close()
