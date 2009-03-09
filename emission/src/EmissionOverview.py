# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.LocationBox import LocationBox
from Components.MenuList import MenuList
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.FileList import FileList
from Components.Label import Label
from Components.Pixmap import Pixmap

from Components.config import config

from enigma import eTimer, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, gFont

import base64
from transmission import transmission

import EmissionDetailview
import EmissionSetup

class EmissionOverviewList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setItemHeight(30)

	def buildListboxEntry(self, torrent):
		size = self.l.getItemSize()

		# XXX: status icons would be nice :-)
		if torrent.status == "downloading":
			eta = str(torrent.eta or '?:??:??')
			return [
				torrent,
				(eListboxPythonMultiContent.TYPE_TEXT, 1, 1, size.width() - 95, 24, 0, RT_HALIGN_LEFT, torrent.name.encode('utf-8', 'ignore')),
				(eListboxPythonMultiContent.TYPE_TEXT, size.width() - 90, 1, 89, 24, 0, RT_HALIGN_RIGHT, eta.encode('utf-8', 'ignore')),
				(eListboxPythonMultiContent.TYPE_PROGRESS, 1, 24, size.width(), 6, int(torrent.progress)),
			]
		return [
			torrent,
			(eListboxPythonMultiContent.TYPE_TEXT, 1, 1, size.width() - 2, 24, 0, RT_HALIGN_LEFT, torrent.name.encode('utf-8', 'ignore')),
			(eListboxPythonMultiContent.TYPE_PROGRESS, 1, 24, size.width(), 6, int(torrent.progress)),
		]

class TorrentLocationBox(LocationBox):
	def __init__(self, session):
		# XXX: implement bookmarks
		LocationBox.__init__(self, session)

		self.skinName = "LocationBox"

		# non-standard filelist which shows .tor(rent) files
		self["filelist"] = FileList(None, showDirectories = True, showFiles = True, matchingPattern = "^.*\.tor(rent)?")

	def ok(self):
		# changeDir in booklist and only select path
		if self.currList == "filelist":
			if self["filelist"].canDescent():
				self["filelist"].descent()
				self.updateTarget()
			else:
				self.select()
		else:
			self["filelist"].changeDir(self["booklist"].getCurrent())

	def selectConfirmed(self, ret):
		if ret:
			dir = self["filelist"].getCurrentDirectory()
			cur = self["filelist"].getSelection()
			ret = dir and cur and dir + cur[0]
			if self.realBookmarks:
				if self.autoAdd and not ret in self.bookmarks:
					self.bookmarks.append(self.getPreferredFolder())
					self.bookmarks.sort()

				if self.bookmarks != self.realBookmarks.value:
					self.realBookmarks.value = self.bookmarks
					self.realBookmarks.save()
			self.close(ret)

	def select(self):
		# only go to work if a file is selected
		if self.currList == "filelist":
			if not self["filelist"].canDescent():
				self.selectConfirmed(True)

class EmissionOverview(Screen, HelpableScreen):
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
		HelpableScreen.__init__(self)

		self.transmission = transmission.Client(
			address = config.plugins.emission.hostname.value,
			port = config.plugins.emission.port.value,
			user = config.plugins.emission.username.value,
			password = config.plugins.emission.password.value
		)

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"ok": (self.ok, _("show details")),
			"cancel": (self.close, _("close")),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green": (self.configure, _("open setup")),
			"yellow": (self.prevlist, _("show previous list")),
			"blue": (self.nextlist, _("show next list")),
		})

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
		{
			"menu": (self.menu, _("open context menu")),
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

	def newDl(self, ret = None):
		if ret:
			if self.transmission.add_url(ret):
				# XXX: talk to me said the user :-)
				print "added"
			else:
				print "hmmm"

	def menuCallback(self, ret = None):
		if ret:
			ret = ret[1]
			if ret == "newDl":
				self.session.openWithCallback(
					self.newDl,
					TorrentLocationBox
				)

	def menu(self):
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			_("What do you want to do?"),
			[(_("Add new download"), "newDl")],
		)

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

	def prevItem(self):
		self['list'].up()
		cur = self['list'].getCurrent()
		return cur and cur[0]

	def nextItem(self):
		self['list'].down()
		cur = self['list'].getCurrent()
		return cur and cur[0]

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
			# XXX: some hint in gui would be nice
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
				cur,
				self.prevItem,
				self.nextItem,
			)

	def close(self):
		self.timer.stop()
		Screen.close(self)

