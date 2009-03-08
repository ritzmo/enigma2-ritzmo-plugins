# -*- coding: utf-8 -*-

#
# note to myself:
# using transmission(rpc) now since it pretty much just works
#

from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Button import Button

from enigma import eTimer, eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont

from transmission import transmission

import EmissionDetailview

class EmissionOverviewList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setItemHeight(24)

	def buildListboxEntry(self, torrent):
		size = self.l.getItemSize()

		return [
			torrent,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 1, size.width() - 10, size.height(), 0, RT_HALIGN_LEFT, torrent.name.encode('utf-8', 'ignore'))
		]

class EmissionOverview(Screen):
	skin = """<screen name="EmissionOverview" title="Torrent Overview" position="75,155" size="565,280">
		<widget name="list" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		# defaults only for now
		self.transmission = transmission.Client()

		self["SetupActions"] = ActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"cancel": self.close,
		})

		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		# note:
		# This should give some kind of overview actually (currently only name)
		# maybe differents types of lists (unrelated) like in original transmission client
		self['list'] = EmissionOverviewList([])
		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def updateList(self, *args, **kwargs):
		list = self.transmission.list().values()
		self.list = [(x,) for x in list]
		self['list'].setList(self.list)
		self.timer.startLongTimer(10)

	def ok(self):
		cur = self['list'].getCurrent()
		if cur:
			cur = cur and cur[0]
			#reload(EmissionDetailview)
			self.timer.stop()
			self.session.openWithCallback(
				self.updateList,
				EmissionDetailview.EmissionDetailview,
				self.transmission,
				cur
			)

			print "[EmissionOverview] ok", cur

	# XXX: some way to add new torrents would be nice
	# they could be loaded from the harddisk or via twisted
	# we might also implement a filescanner later on

	def close(self):
		self.timer.stop()
		Screen.close(self)

