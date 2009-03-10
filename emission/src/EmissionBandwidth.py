# GUI (Screens)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap

# Configuration
from Components.config import config, getConfigListEntry, \
	ConfigNumber, ConfigSelection

class EmissionBandwidth(Screen, ConfigListScreen):
	def __init__(self, session, val, isTorrent):
		Screen.__init__(self, session)
		self.skinName = "Setup"

		# Summary
		self.setup_title = _("Bandwidth settings")
		self.onChangedEntry = []

		ConfigListScreen.__init__(self, [], session = session, on_change = self.changed)

		if isTorrent:
			self.downloadLimitMode = ConfigSelection(choices = [(0, _("Global Setting")), (2, _("Unlimited")), (1, _("Limit"))], default = val.downloadLimitMode)
			self.downloadLimit = ConfigNumber(default = val.downloadLimit)
			self.uploadLimitMode = ConfigSelection(choices = [(0, _("Global Setting")), (2, _("Unlimited")), (1, _("Limit"))], default = val.uploadLimitMode)
			self.uploadLimit = ConfigNumber(default = val.uploadLimit)
			self.maxConnectedPeers = ConfigNumber(default = val.maxConnectedPeers)
		else:
			self.downloadLimitMode = ConfigSelection(choices = [(0, _("Unlimited")), (1, _("Limit"))], default = val.speed_limit_down_enabled)
			self.downloadLimit = ConfigNumber(default = val.speed_limit_down)
			self.uploadLimitMode = ConfigSelection(choices = [(0, _("Unlimited")), (1, _("Limit"))], default = val.speed_limit_up_enabled)
			self.uploadLimit = ConfigNumber(default = val.speed_limit_up)
			self.maxConnectedPeers = ConfigNumber(default = val.peer_limit)

		self.downloadLimitMode.addNotifier(self.updateList, initial_call = False)
		self.uploadLimitMode.addNotifier(self.updateList, initial_call = False)

		self.updateList()

		# Initialize widgets
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()
		# XXX: this looks stupid in the default skin :-)
		self["title"] = Label(_("%s bandwidth settings") % (isTorrent and val.name or "eMission"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def updateList(self, *args):
		list = [
			getConfigListEntry(_("Download rate"), self.downloadLimitMode)
		]
		if self.downloadLimitMode.value == 1:
			list.append(getConfigListEntry(_("Limit"), self.downloadLimit))
		list.append(getConfigListEntry(_("Upload rate"), self.uploadLimitMode))
		if self.uploadLimitMode.value == 1:
			list.append(getConfigListEntry(_("Limit"), self.uploadLimit))
		list.append(getConfigListEntry(_("Maximum Connections"), self.maxConnectedPeers))
		self["config"].setList(list)

	def setCustomTitle(self):
		self.setTitle(_("Configure eMission"))

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
		if self.downloadLimitMode.value == 2 or self.uploadLimitMode.value == 2:
			self.session.open(
					MessageBox,
					_("Setting \"Unlimited\" is unsupported through RPC.\nEither abort or choose another limit."),
					type = MessageBox.TYPE_ERROR
			)
		else:
			self.close({
				'speed_limit_down_enabled': self.downloadLimitMode.value,
				'speed_limit_down': self.downloadLimit.value,
				'speed_limit_up_enabled': self.uploadLimitMode.value,
				'speed_limit_up': self.uploadLimit.value,
				'peer_limit': self.maxConnectedPeers.value,
			})

