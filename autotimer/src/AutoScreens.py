# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection

# GUI (Components)
from AutoList import AutoList
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, ConfigText, ConfigClock, ConfigInteger, ConfigSelection

# Timer
from RecordTimer import AFTEREVENT

# Needed to convert our timestamp back and forth
from time import localtime, mktime

# Show ServiceName instead of ServiceReference
from ServiceReference import ServiceReference

# Plugin
from AutoTimerComponent import AutoTimerComponent

class AutoChannelEdit(Screen, ConfigListScreen):
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

		self.list = [
			getConfigListEntry("Enable Channel Restriction", ConfigEnableDisable(default = servicerestriction))
		]

		self.list.extend([
			getConfigListEntry("Allowed Channel", ConfigSelection(choices = [(str(x), ServiceReference(str(x)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode("UTF-8"))]))
				for x in servicelist
		])

		ConfigListScreen.__init__(self, self.list, session = session)

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
			list.append(getConfigListEntry("Allowed Channel", ConfigSelection(choices = [(args[0].toString(), ServiceReference(args[0]).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode("UTF-8"))])))
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

class AutoTimerEdit(Screen, ConfigListScreen):
	skin = """<screen name="AutoTimerEdit" title="Edit AutoTimer" position="130,150" size="450,280">
		<widget name="config" position="5,5" size="440,235" scrollbarMode="showOnDemand" />
		<ePixmap position="0,240" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,240" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="310,240" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="310,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timer):
		Screen.__init__(self, session)

		# We need to keep our Id
		self.uniqueTimerId = timer.id

		# TODO: implement configuration for these - for now we just keep them
		self.excludes = timer.exclude
		self.maxduration = timer.maxduration

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

		self.refresh()

		ConfigListScreen.__init__(self, self.list, session = session)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Edit Channels"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
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
		self.enabled = ConfigEnableDisable(default = timer.enabled)

	def refresh(self):
		# First two entries are always shown
		self.list = [
			getConfigListEntry(_("Enabled"), self.enabled),
			getConfigListEntry("Match Title", self.name),
			getConfigListEntry("Only match during Timespan", self.timespan)
		]

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.list.extend([
				getConfigListEntry("Begin of Timespan", self.timespanbegin),
				getConfigListEntry("End of Timespan", self.timespanend)
			])

		self.list.append(getConfigListEntry("Custom offset", self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			self.list.extend([
				getConfigListEntry("Offset before recording (in m)", self.offsetbegin),
				getConfigListEntry("Offset after recording (in m)", self.offsetend)
			])

		self.list.append(getConfigListEntry(_("After event"), self.afterevent))

	def reloadList(self, value):
		self.refresh()
		self["config"].setList(self.list)

	def editChannels(self):
		self.session.openWithCallback(
			self.editCallback,
			AutoChannelEdit,
			self.serviceRestriction,
			self.services
		)

	def editCallback(self, ret):
		if ret:
			self.serviceRestriction = ret[0]
			self.services = ret[1] 

	def cancel(self):
		self.close(None)

	def save(self):
		# Create new tuple

		# Timespan
		if self.timespan.value:
			start = self.timespanbegin.value
			end = self.timespanend.value
			timetuple = (start, end)
		else:
			timetuple= None

		# Services
		if self.serviceRestriction:
			servicelist = self.services
		else:
			servicelist = None

		# Offset
		if self.offset.value:
			offset = (self.offsetbegin.value*60, self.offsetend.value*60)
		else:
			offset = None

		# AfterEvent
		afterevent = {"nothing": AFTEREVENT.NONE, "deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY}[self.afterevent.value]

		# Close and return tuple
		self.close(AutoTimerComponent(
			self.uniqueTimerId,
			self.name.value,
			self.enabled.value,
			timespan = timetuple,
			services = servicelist,
			offset = offset,
			afterevent = afterevent,
			exclude = self.excludes,
			maxduration = self.maxduration
		))

class AutoTimerOverview(Screen):
	skin = """
		<screen name="AutoTimerOverview" position="140,148" size="420,250" title="AutoTimer Overview">
			<widget name="entries" position="5,0" size="410,200" scrollbarMode="showOnDemand" />
			<ePixmap position="0,205" zPosition="1" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<ePixmap position="140,205" zPosition="1" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="280,205" zPosition="1" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="0,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="140,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="280,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, autotimer):
		Screen.__init__(self, session)

		# Save autotimer and read in Xml
		self.autotimer = autotimer
		try:
			self.autotimer.readXml()
		except:
			# Don't crash during development
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		# Button Labels
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Add"))

		# Create List of Timers
		self["entries"] = AutoList(autotimer.getTupleTimerList())

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.ok,
				"cancel": self.cancel,
				"green": self.save,
				"yellow": self.remove,
				"blue": self.add
			}
		)

	def add(self):
		self.session.openWithCallback(
			self.editCallback,
			AutoTimerEdit,
			# TODO: implement setting a default?
			AutoTimerComponent(
				self.autotimer.getUniqueId(),	# Id
				"",								# Name
				True							# Enabled				
			)
		)

	def refresh(self):
		# Re-assign List
		self["entries"].setList(self.autotimer.getTupleTimerList())

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerEdit,
				current[0]
			)

	def editCallback(self, res):
		if res is not None:
			self.autotimer.set(res)
			self.refresh()

	def remove(self):
		# Remove selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.autotimer.remove(current[0].id)
			self.refresh()

	def cancel(self):
		self.close(None)

	def save(self):
		# Save Xml
		try:
			self.autotimer.writeXml()
		except:
			# Don't crash during development
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		# Nothing else to be done?
		self.close(self.session)