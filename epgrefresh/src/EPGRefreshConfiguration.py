# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from EPGRefreshChannelEditor import EPGRefreshChannelEditor

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import config, getConfigListEntry

from EPGRefresh import epgrefresh

from sets import Set

class EPGRefreshConfiguration(Screen, ConfigListScreen):
	"""Configuration of EPGRefresh"""

	skin = """<screen name="EPGRefreshConfiguration" title="Configure EPGRefresh" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "EPGRefresh Configuration"
		self.onChangedEntry = []

		# -
		self.servicelist = epgrefresh.services

		self.list = [
			getConfigListEntry(_("Refresh automatically"), config.plugins.epgrefresh.enabled),
			getConfigListEntry(_("Time to stay on service (in m)"), config.plugins.epgrefresh.interval),
			getConfigListEntry(_("Refresh EPG after"), config.plugins.epgrefresh.begin),
			getConfigListEntry(_("Refresh EPG before"), config.plugins.epgrefresh.end),
			getConfigListEntry(_("Inherit Services from AutoTimer if available"), config.plugins.epgrefresh.inherit_autotimer),
		]

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Edit Channels"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"blue": self.editChannels
			}
		)

		# Trigger change
		self.changed()

	def editChannels(self):
		self.session.openWithCallback(
			self.editChannelsCallback,
			EPGRefreshChannelEditor,
			self.servicelist
		)

	def editChannelsCallback(self, ret):
		if ret:
			self.servicelist = ret

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

	def keySave(self):
		epgrefresh.services = Set(self.servicelist)
		try:
			epgrefresh.saveConfiguration()
		except Exception, e:
			print "[EPGRefresh] Error occured while saving configuration:", e

		ConfigListScreen.keySave(self)
