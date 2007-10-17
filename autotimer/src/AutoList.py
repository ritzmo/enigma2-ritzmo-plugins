# GUI (Components)
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT#, RT_HALIGN_RIGHT

class AutoList(GUIComponent):
	"""Defines a simple Component to show Timer name"""
	
	def __init__(self, entries):
		GUIComponent.__init__(self)

		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(self.list)

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(25)

	def buildListboxEntry(self, timer):
		res = [ None ]
		width = self.l.getItemSize().width()
		if timer.enabled:
			# Append with default color
			res.append(MultiContentEntryText(pos=(5, 5), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = timer.name))
		else:
			# Append with grey as color
			res.append(MultiContentEntryText(pos=(5, 5), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = timer.name, color = int("#bcbbbc"[1:], 0x10)))

		return res

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def setList(self, l):
		return self.l.setList(l)