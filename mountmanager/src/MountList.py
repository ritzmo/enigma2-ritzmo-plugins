# GUI (Components)
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_HALIGN_RIGHT

class MountList(MenuList):
	"""Defines a simple Component to show Mountpoint & status"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, eListboxPythonMultiContent)

		# Cache these
		self.active = _("enabled")
		self.inactive = _("disabled")

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(50)

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
