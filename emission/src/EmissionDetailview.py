# -*- coding: utf-8 -*-

#
# note to myself:
# using transmission(rpc) now since it pretty much just works
#

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label

from enigma import eTimer

class EmissionDetailview(Screen):
	skin = """<screen name="EmissionDetailview" title="Torrent View" position="75,155" size="565,280">
		<eLabel position="420,5" text="DL: " size="50,20" font="Regular;18" transparent="1" />
		<widget name="downspeed" position="470,5" size="85,20" halign="right" font="Regular;18" transparent="1" />
		<eLabel position="420,27" text="UL: " size="50,20" font="Regular;18" transparent="1" />
		<widget name="upspeed" position="470,27" size="85,20" halign="right" font="Regular;18" transparent="1" />
		<widget name="name" position="5,5" size="420,22" font="Regular;18" transparent="1" />
		<widget name="peers" position="5,27" size="545,22" font="Regular;18" transparent="1" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, daemon, torrent):
		Screen.__init__(self, session)
		self.transmission = daemon
		self.torrentid = torrent.id

		self["SetupActions"] = ActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"cancel": self.close,
		})

		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["upspeed"] = Label("")
		self["downspeed"] = Label("")
		self["peers"] = Label("")
		self["name"] = Label(torrent.name) # this should be pretty constant so we only set it once

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def updateList(self, *args, **kwargs):
		id = self.torrentid
		torrent = self.transmission.info([id])[id]
		self["upspeed"].setText(_("%d kb/s") % (torrent.rateUpload / 1024))
		self["downspeed"].setText(_("%d kb/s") % (torrent.rateDownload / 1024))
		self["peers"].setText(_("Downloading from %d of %d peers") % (torrent.peersSendingToUs, torrent.peersConnected))
		self.timer.startLongTimer(3)

	def ok(self):
		print "[EmissionDetailview] ok"

	def close(self):
		self.timer.stop()
		Screen.close(self)

