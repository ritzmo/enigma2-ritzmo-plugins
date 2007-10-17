# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChoiceBox import ChoiceBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, ConfigText

class AutoTimerExcludeEditor(Screen, ConfigListScreen):
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

		ConfigListScreen.__init__(self, self.list, session = session)

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

	def remove(self):
		idx = self["config"].getCurrentIndex()
		if idx:
			if idx < self.lenTitles:
				self.lenTitles -= 1
			elif idx < self.lenShorts:
				self.lenShorts -= 1

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
				(_("Description"), 2)
			]
			
		)

	def typeSelected(self, ret):
		if ret is not None:
			list = self["config"].getList()

			if ret[1] == 0:
				pos = self.lenTitles
				self.lenTitles += 1
				text = _("Filter in Title")
			elif ret[1] == 1:
				pos = self.lenShorts
				self.lenShorts += 1
				text = _("Filter in Shortdescription")
			else:
				pos = len(list)
				text = _("Filter in Description")

			
			list.insert(pos, getConfigListEntry(text, ConfigText(fixed_size = False)))
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		list = self["config"].getList()
		restriction = list.pop(0)

		# Warning, accessing a ConfigListEntry directly might be considered evil!

		idx = 0
		titles = []
		shorts = []
		desc = []
		for item in list:
			# Skip empty entries
			if item[1].value == "":
				idx += 1
				continue
			if idx < self.lenTitles:
				titles.append(item[1].value.encode("UTF-8"))
			elif idx < self.lenShorts:
				shorts.append(item[1].value.encode("UTF-8"))
			else:
				desc.append(item[1].value.encode("UTF-8"))
			idx += 1

		self.close((
			restriction[1].value,
			(titles, shorts, desc)
		))
