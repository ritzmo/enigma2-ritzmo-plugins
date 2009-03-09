# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.Progress import Progress

from enigma import eTimer

class EmissionDetailview(Screen, HelpableScreen):
	skin = """<screen name="EmissionDetailview" title="Torrent View" position="75,155" size="565,280">
		<eLabel position="420,5" text="DL: " size="50,20" font="Regular;18" transparent="1" />
		<widget name="downspeed" position="470,5" size="85,20" halign="right" font="Regular;18" transparent="1" />
		<eLabel position="420,27" text="UL: " size="50,20" font="Regular;18" transparent="1" />
		<widget name="upspeed" position="470,27" size="85,20" halign="right" font="Regular;18" transparent="1" />
		<widget name="name" position="5,5" size="420,22" font="Regular;18" transparent="1" />
		<widget name="peers" position="5,27" size="545,22" font="Regular;18" transparent="1" />
		<eLabel text="Files" position="5,65" size="100,20" font="Regular;18" transparent="1" />
		<widget source="files" render="Listbox" position="5,85" size="560,110" transparent="1" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
						MultiContentEntryText(pos=(2,2), size=(560,22), text = 4, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,26), size=(110,20), text = "Downloaded", font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(117,26), size=(100,20), text = 2, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(388,26), size=(70,20), text = "Total", font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(458,26), size=(100,20), text = 5, font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(220,26), size=(180,20), text = 6, font = 1, flags = RT_VALIGN_CENTER),
					],
				  "fonts": [gFont("Regular", 20),gFont("Regular", 18)],
				  "itemHeight": 46
				 }
			</convert>
		</widget>
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
		HelpableScreen.__init__(self)
		self.transmission = daemon
		self.torrentid = torrent.id

		# XXX: implement next/previous dl?

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"ok": (self.ok, _("toggle file status")),
			"cancel": self.close,
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"yellow": (self.yellow, _("toggle download status")),
			"blue": (self.blue, _("remove torrent"))
		})

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button("")
		if torrent.status == "stopped":
			self["key_yellow"] = Button(_("start"))
		else:
			self["key_yellow"] = Button(_("stop"))
		self["key_blue"] = Button(_("remove"))

		self["upspeed"] = Label("")
		self["downspeed"] = Label("")
		self["peers"] = Label("")
		self["name"] = Label(torrent.name) # this should be pretty constant so we only set it once
		self["files"] = List([])
		self["progress"] = Progress(torrent.progress)

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def yellow(self):
		id = self.torrentid
		torrent = self.transmission.info([id])[id]
		status = torrent.status
		if status == "stopped":
			self.transmission.start([id])
			self["key_yellow"].setText(_("pause"))
		elif status in ("downloading", "seeding"):
			self.transmission.stop([id])
			self["key_yellow"].setText(_("start"))

	def blue(self):
		self.session.openWithCallback(
			self.removeCallback,
			ChoiceBox,
			_("Really delete torrent?"),
			[(_("no"), "no"),
			(_("yes"), "yes"),
			(_("yes, including data"), "data")]
		)

	def removeCallback(self, ret = None):
		if ret:
			ret = ret[1]
			if ret == "yes":
				self.transmission.remove([self.torrentid], delete_data = False)
			elif ret == "data":
				self.transmission.remove([self.torrentid], delete_data = True)

	def updateList(self, *args, **kwargs):
		id = self.torrentid
		torrent = self.transmission.info([id])[id]

		self["upspeed"].setText(_("%d kb/s") % (torrent.rateUpload / 1024))
		self["downspeed"].setText(_("%d kb/s") % (torrent.rateDownload / 1024))
		self["progress"].setValue(torrent.progress)

		status = torrent.status
		if status == 'check pending':
			peerText = _("check pending") # ???
		elif status == 'checking':
			peerText = _("checking")
		elif status == 'downloading':
			peerText = _("Downloading from %d of %d peers") % (torrent.peersSendingToUs, torrent.peersConnected)
		elif status == 'seeding':
			peerText = _("Seeding to %d of %d peers") % (torrent.peersGettingFromUs, torrent.peersConnected)
		elif status == 'stopped':
			peerText = _("stopped")
		self["peers"].setText(peerText)

		l = []
		files = torrent.files()
		for id in files:
			x = files[id]
			# x is dict: 'priority': 'normal', 'completed': 340237462, 'selected': True, 'name': 'btra5328500k.wmv', 'size': 508566678
			l.append((id, x['priority'], str(x['completed']/1048576) + " MB", \
				x['selected'], x['name'], str(x['size']/1048576) + " MB", \
				x['selected'] and _("downloading") or _("skipping")
			))
		self["files"].updateList(l)

		self.timer.startLongTimer(5)

	def ok(self):
		cur = self["files"].getCurrent()
		if cur and False: # set_files broken in transmissionrpc :-) 
			self.transmission.set_files({
				self.torrentid: {
					cur[0]: {
						'priority': cur[1],
						'selected': not cur[3]
					}
				}
			})

	def close(self):
		self.timer.stop()
		Screen.close(self)

