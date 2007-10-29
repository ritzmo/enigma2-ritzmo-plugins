# GUI (Screens)
from Screens.Screen import Screen

# Plugin
from Plugins.Plugin import PluginDescriptor

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER

from ServiceReference import ServiceReference

class SimpleServiceList(GUIComponent):
	"""---"""
	
	def __init__(self, entries):
		GUIComponent.__init__(self)

		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(self.list)

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(25)

	def buildListboxEntry(self, bouquetref, serviceref):
		res = [ None ]
		width = self.l.getItemSize().width()

		text = ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')

		res.append(MultiContentEntryText(pos=(0, 0), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = text))

		return res

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def setList(self, l):
		return self.l.setList(l)

class HistoryBrowser(Screen):
	"""..."""

	skin = """<screen name="HistoryBrowser" position="100,130" size="540,280" >
			<widget name="history" position="0,0" size="540,230" />
			<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, servicelist):
		Screen.__init__(self, session)
		self.servicelist = servicelist

		tuplehistory = [(x[0], x[1]) for x in self.servicelist.history]
		tuplehistory.reverse()

		self["history"] = SimpleServiceList(tuplehistory)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"cancel": self.cancel
		})

	def ok(self):
		cur = self["history"].getCurrent()
		if cur:
			# TODO: this seems buggy
			if self.servicelist.getRoot() != cur[0]: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != cur[0]:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(cur[0])
			self.servicelist.setCurrentSelection(cur[1])
			self.servicelist.zap()
		self.close() # TODO: do we really want to close here?

	def cancel(self):
		self.close()

# Mainfunction
def main(session, servicelist, **kwargs):
	session.open(
		HistoryBrowser,
		servicelist
	)

def Plugins(**kwargs):
 	return [PluginDescriptor(name="History browser", description="???", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
