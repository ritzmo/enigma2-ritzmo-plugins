# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap

from Components.config import config

from enigma import eTimer, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont

from transmission import transmission

import EmissionDetailview
import EmissionSetup

class EmissionOverviewList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setItemHeight(24)

	def buildListboxEntry(self, torrent):
		size = self.l.getItemSize()

		if torrent.status == "downloading":
			eta = str(torrent.eta or '?:??:??')
		else:
			eta = ""

		# XXX: status icons would be nice :-)

		return [
			torrent,
			(eListboxPythonMultiContent.TYPE_TEXT, 1, 1, size.width() - 85, size.height(), 0, RT_HALIGN_LEFT, torrent.name.encode('utf-8', 'ignore')),
			(eListboxPythonMultiContent.TYPE_TEXT, size.width() - 80, 1, 79, size.height(), 0, RT_HALIGN_RIGHT, eta.encode('utf-8', 'ignore'))
		]

class EmissionOverview(Screen):
	skin = """<screen name="EmissionOverview" title="Torrent Overview" position="75,155" size="565,300">
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="all_sel" pixmap="skin_default/epg_now.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="5,10" zPosition="2" name="all_text" halign="center" font="Regular;18" />
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="downloading_sel" pixmap="skin_default/epg_next.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="111,10" zPosition="2" name="downloading_text" halign="center" font="Regular;18" />
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="seeding_sel" pixmap="skin_default/epg_more.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="200,10" zPosition="2" name="seeding_text" halign="center" font="Regular;18" />
		<widget name="list" position="5,30" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,260" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,260" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,260" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,260" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,260" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,260" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,260" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,260" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	LIST_TYPE_ALL = 0
	LIST_TYPE_DOWNLOADING = 1
	LIST_TYPE_SEEDING = 2

	def __init__(self, session):
		Screen.__init__(self, session)
		self.transmission = transmission.Client(
			address = config.plugins.emission.hostname.value,
			port = config.plugins.emission.port.value,
			user = config.plugins.emission.username.value,
			password = config.plugins.emission.password.value
		)

		self["SetupActions"] = ActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"cancel": self.close,
		})

		self["ColorActions"] = ActionMap(["ColorActions"],
		{
			"green": self.configure,
			"yellow": self.prevlist,
			"blue": self.nextlist,
		})

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Configure"))
		self["key_yellow"] = Button(_("Seeding"))
		self["key_blue"] = Button(_("Download"))

		self["all_text"] = Label(_("All"))
		self["downloading_text"] = Label(_("DL"))
		self["seeding_text"] = Label(_("UL"))

		self.list_type = self.LIST_TYPE_ALL

		self["all_sel"] = Pixmap()
		self["downloading_sel"] = Pixmap()
		self["downloading_sel"].hide()
		self["seeding_sel"] = Pixmap()
		self["seeding_sel"].hide()

		# This should actually give some kind of overview (currently just name and eta or is this enough?)
		self['list'] = EmissionOverviewList([])

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def showHideSetTextMagic(self):
		if self.list_type == self.LIST_TYPE_ALL:
			self["all_sel"].show()
			self["downloading_sel"].hide()
			self["seeding_sel"].hide()
			self["key_yellow"].setText(_("Seeding"))
			self["key_blue"].setText(_("Download"))
		elif self.list_type == self.LIST_TYPE_DOWNLOADING:
			self["all_sel"].hide()
			self["downloading_sel"].show()
			self["seeding_sel"].hide()
			self["key_yellow"].setText(_("All"))
			self["key_blue"].setText(_("Seeding"))
		elif self.list_type == self.LIST_TYPE_SEEDING:
			self["all_sel"].hide()
			self["downloading_sel"].hide()
			self["seeding_sel"].show()
			self["key_yellow"].setText(_("Download"))
			self["key_blue"].setText(_("Seeding"))

	def prevlist(self):
		self.timer.stop()
		if self.list_type == self.LIST_TYPE_ALL:
			self.list_type = self.LIST_TYPE_SEEDING
		elif self.list_type == self.LIST_TYPE_DOWNLOADING:
			self.list_type = self.LIST_TYPE_ALL
		elif self.list_type == self.LIST_TYPE_SEEDING:
			self.list_type = self.LIST_TYPE_DOWNLOADING
		self.showHideSetTextMagic()
		self.updateList()

	def nextlist(self):
		self.timer.stop()
		if self.list_type == self.LIST_TYPE_ALL:
			self.list_type = self.LIST_TYPE_DOWNLOADING
		elif self.list_type == self.LIST_TYPE_DOWNLOADING:
			self.list_type = self.LIST_TYPE_SEEDING
		elif self.list_type == self.LIST_TYPE_SEEDING:
			self.list_type = self.LIST_TYPE_ALL
		self.showHideSetTextMagic()
		self.updateList()

	def configureCallback(self):
		self.transmission = transmission.Client(
			address = config.plugins.emission.hostname.value,
			port = config.plugins.emission.port.value,
			user = config.plugins.emission.username.value,
			password = config.plugins.emission.password.value
		)
		self.updateList()

	def configure(self):
		reload(EmissionSetup)
		self.timer.stop()
		self.session.openWithCallback(
			self.configureCallback,
			EmissionSetup.EmissionSetup
		)

	def updateList(self, *args, **kwargs):
		try:
			list = self.transmission.list().values()
		except transmission.TransmissionError:
			list = []
		if self.list_type == self.LIST_TYPE_ALL:
			self.list = [(x,) for x in list]
		elif self.list_type == self.LIST_TYPE_DOWNLOADING:
			self.list = [(x,) for x in list if x.status == "downloading"]
		elif self.list_type == self.LIST_TYPE_SEEDING:
			self.list = [(x,) for x in list if x.status == "seeding"]

		self['list'].setList(self.list)
		self.timer.startLongTimer(10)

	def ok(self):
		cur = self['list'].getCurrent()
		if cur:
			cur = cur and cur[0]
			reload(EmissionDetailview)
			self.timer.stop()
			self.session.openWithCallback(
				self.updateList,
				EmissionDetailview.EmissionDetailview,
				self.transmission,
				cur
			)

	# XXX: some way to add new torrents would be nice
	# they could be loaded from the harddisk or via twisted
	# we might also implement a filescanner later on

	def close(self):
		self.timer.stop()
		Screen.close(self)

