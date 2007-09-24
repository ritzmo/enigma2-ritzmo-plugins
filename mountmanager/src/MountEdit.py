from Screens.Screen import Screen
from Components.config import getConfigListEntry, ConfigSelection, ConfigEnableDisable, ConfigText, ConfigIP
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button

class MountEdit(Screen, ConfigListScreen):
	skin = """
		<screen name="MountEdit" position="130,150" size="450,240" title="Mount editor">
			<widget name="config" position="0,0" size="450,200" scrollbarMode="showOnDemand" />
			<ePixmap position="0,200" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,200" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, mounts, org_mp = None):
		Screen.__init__(self, session)

		# Needed to get Tuple and to save
		self.mounts = mounts

		# Wee need to keep mp as this is our identifier
		self.mountpoint = org_mp
		self.initialize(org_mp)

		# We need to change shown items, so add a notifier to type
		self.type.addNotifier(self.typeChanged, initial_call = False)

		# Generate self.list dependant on mount type
		self.refresh()

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
                self["key_green"] = Button(_("OK"))

		# Init ConfigListScreen
		ConfigListScreen.__init__(self, self.list, session = session)

		self["setupActions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.close,
				"ok": self.ok,
				"save": self.ok
			}, -1
		)

	def initialize(self, mp):
		# Always set these as we might switch type
		options = "rw,nolock"
		username = ""
		password = ""

		# Get Tuple
		realValues = self.mounts.getTuple(mp)

		# If we have tuple extract config
		if realValues is not None:
			type = realValues[0]
			if realValues[1] == "1":
				active = True
			else:
				active = False
			server = [ int(x) for x in realValues[2].split('.')]
			dir = realValues[4]
			share = realValues[3]
			if type == "nfs":
				options = realValues[5]
			else:
				username = realValues[5]
				password = realValues[6]
		# Else set defaults
		else:
			type = "nfs"
			active = True
			# TODO: base this on ip of main intf?
			server = [192, 168, 0, 0]
			share = "/export/hdd"
			dir = "/media/net"

		# Initialize Config Elements
		self.type = ConfigSelection(default = type, choices = ["nfs","cifs"])
		self.active = ConfigEnableDisable(default = active)
		self.server = ConfigIP(default = server)
		self.share = ConfigText(default = share, fixed_size = False)
		self.dir = ConfigText(default = dir, fixed_size = False)
		self.options = ConfigText(default = options, fixed_size = False)
		self.username = ConfigText(default = username, fixed_size = False) 
		self.password = ConfigText(default = password, fixed_size = False)

	def typeChanged(self, value):
		# Refresh self.list and inform config
		self.refresh()
		self["config"].l.setList(self.list)

	def refresh(self):
		# Always in List
		self.list = [
			getConfigListEntry(_("Mount type"), self.type),
			getConfigListEntry(_("Active"), self.active),
			getConfigListEntry(_("Server IP"), self.server),
			getConfigListEntry(_("Server share"), self.share),
			getConfigListEntry(_("Local directory"), self.dir)
		]

		# Append Options if type is nfs
		if self.type.value == "nfs":
			self.list.append(getConfigListEntry(_("Mount options"), self.options))
		# Append Username/Password if type is not nfs (type is cifs)
		else:
			self.list.extend([
				getConfigListEntry(_("Username"), self.username),
				getConfigListEntry(_("Password"), self.password)
			])

	def ok(self):
		# Translate back "active"
		if self.active.value:
			active = "1"
		else:
			active = "0"

		# Create NFS-Tuple
		if self.type.value == "nfs":
			newTuple = (
				"nfs",
				active,
				'.'.join([str(x) for x in self.server.value]),
				self.share.value,
				self.dir.value,
				self.options.value
			)
		# Create Cifs-Tuple
		else:
			newTuple = (
				"cifs",
				active,
				'.'.join([str(x) for x in self.server.value]),
				self.share.value,
				self.dir.value,
				self.username.value,
				self.password.value
			)

		# Append tuple and close dialog afterwards
		self.mounts.setTuple(self.mountpoint, newTuple)
		self.close()
