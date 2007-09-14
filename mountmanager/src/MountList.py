from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT

class MountList(GUIComponent):
	def __init__(self, entries):
		GUIComponent.__init__(self)

		# Cache these
		self.active = _("enabled")
		self.inactive = _("disabled")

		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(self.list)

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(50)

	def buildListboxEntry(self, mountpoint, active):
		res = [ None ]
		width = self.l.getItemSize().width()
		res.append(MultiContentEntryText(pos=(0, 0), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = mountpoint.encode("UTF-8")))

		# Make active human-readable
		if active == "1":
			act = self.active
		else:
			act = self.inactive

		res.append(MultiContentEntryText(pos=(0, 25), size=(width, 20), font=1, flags = RT_HALIGN_RIGHT, text = act))

		return res

	def getCurrent(self):
		return self.l.getCurrentSelection()
