# -*- coding: utf-8 -*-

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen

# GUI (Components)
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.Progress import Progress

from enigma import eTimer

import EmissionBandwidth

class EmissionDetailview(Screen, HelpableScreen):
	skin = """<screen name="EmissionDetailview" title="Torrent View" position="75,75" size="565,450">
		<eLabel position="450,5" text="DL: " size="30,20" font="Regular;18" />
		<widget name="downspeed" position="480,5" size="85,20" halign="right" font="Regular;18" />
		<eLabel position="450,27" text="UL: " size="30,20" font="Regular;18" transparent="1" />
		<widget name="upspeed" position="480,27" size="85,20" halign="right" font="Regular;18" />
		<widget name="name" position="5,5" size="445,20" font="Regular;18" />
		<widget name="peers" position="5,27" size="555,20" font="Regular;18" />
		<!-- XXX: the actual uri might end up in the next line, this sucks :-) -->
		<widget name="tracker" position="5,50" size="555,20" font="Regular;18" />
		<widget name="private" position="5,73" size="555,20" font="Regular;18" />
		<widget name="eta" position="5,130" size="555,20" font="Regular;18" />
		<widget name="progress_text" position="5,155" size="400,20" font="Regular;18" />
		<widget name="ratio" position="410,155" size="150,20" font="Regular;18" halign="right" />
		<widget source="progress" render="Progress" position="5,180" size="555,6" />
		<widget name="files_text" position="5,190" size="100,20" font="Regular;18" />
		<widget source="files" render="Listbox" position="0,215" size="566,185" scrollbarMode="showAlways">
			<convert type="TemplatedMultiContent">
				{"template": [
						MultiContentEntryText(pos=(2,2), size=(560,22), text = 4, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,26), size=(110,20), text = "Downloaded", font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(117,26), size=(100,20), text = 2, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(365,26), size=(70,20), text = "Total", font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(435,26), size=(100,20), text = 5, font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(220,26), size=(160,20), text = 6, font = 1, flags = RT_VALIGN_CENTER),
						(eListboxPythonMultiContent.TYPE_PROGRESS, 0, 47, 540, 6, -7),
					],
				  "fonts": [gFont("Regular", 20),gFont("Regular", 18)],
				  "itemHeight": 54
				 }
			</convert>
		</widget>
		<ePixmap position="0,405" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,405" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,405" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,405" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,405" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,405" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,405" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,405" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, daemon, torrent, prevFunc = None, nextFunc = None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.transmission = daemon
		self.torrentid = torrent.id
		self.prevFunc = prevFunc
		self.nextFunc = nextFunc

		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
		{
			"prevMarker": (self.prevDl, _("show previous download details")),
			"nextMarker": (self.nextDl, _("show next download details")),
		})

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"ok": (self.ok, _("toggle file status")),
			"cancel": self.close,
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"yellow": (self.toggleStatus, _("toggle download status")),
			"green": (self.bandwidth, _("open bandwidth settings")),
			"blue": (self.remove , _("remove torrent")),
		})

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Bandwidth"))
		if torrent.status == "stopped":
			self["key_yellow"] = Button(_("start"))
		else:
			self["key_yellow"] = Button(_("stop"))
		self["key_blue"] = Button(_("remove"))

		self["upspeed"] = Label("")
		self["downspeed"] = Label("")
		self["peers"] = Label("")
		self["name"] = Label(torrent.name)
		self["files_text"] = Label(_("Files"))
		self["files"] = List([])
		self["progress"] = Progress(int(torrent.progress))
		self["progress_text"] = Label("")
		self["ratio"] = Label("")
		self["eta"] = Label("")
		self["tracker"] = Label("")
		self["private"] = Label("")

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def bandwidthCallback(self, ret = None):
		if ret:
			try:
				self.transmission.change([self.torrentid], **ret)
			except transmission.TransmissionError:
				self.session.open(
					MessageBox,
					_("Could not connect to transmission-daemon!"),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)
		self.updateList()

	def bandwidth(self):
		reload(EmissionBandwidth)
		self.timer.stop()
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
		except transmission.TransmissionError:
			self.session.open(
				MessageBox,
				_("Could not connect to transmission-daemon!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)
			# XXX: this seems silly but cleans the gui and restarts the timer :-)
			self.updateList()
		else:
			self.session.openWithCallback(
				self.bandwidthCallback,
				EmissionBandwidth.EmissionBandwidth,
				torrent,
				True
			)

	def prevDl(self):
		if self.prevFunc:
			torrent = self.prevFunc()
			if torrent:
				self.timer.stop()
				self.torrentid = torrent.id
				self["name"].setText(torrent.name)
				self.updateList()

	def nextDl(self):
		if self.nextFunc:
			torrent = self.nextFunc()
			if torrent:
				self.timer.stop()
				self.torrentid = torrent.id
				self["name"].setText(torrent.name)
				self.updateList()

	def toggleStatus(self):
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
			status = torrent.status
			if status == "stopped":
				self.transmission.start([id])
				self["key_yellow"].setText(_("pause"))
			elif status in ("downloading", "seeding"):
				self.transmission.stop([id])
				self["key_yellow"].setText(_("start"))
		except transmission.TransmissionError:
			self.session.open(
				MessageBox,
				_("Could not connect to transmission-daemon!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

	def remove(self):
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
			try:
				if ret == "yes":
					self.transmission.remove([self.torrentid], delete_data = False)
					self.close()
				elif ret == "data":
					self.transmission.remove([self.torrentid], delete_data = True)
					self.close()
			except transmission.TransmissionError:
				self.session.open(
					MessageBox,
					_("Could not connect to transmission-daemon!"),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)

	def updateList(self, *args, **kwargs):
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
		except transmission.TransmissionError:
			self["upspeed"].setText("")
			self["downspeed"].setText("")
			self["peers"].setText("")
			self["progress_text"].setText("")
			self["ratio"].setText("")
			self["eta"].setText("")
			self["tracker"].setText("")
			self["private"].setText("")
			self["files"].setList([])
		else:
			self["upspeed"].setText(_("%d kb/s") % (torrent.rateUpload / 1024))
			self["downspeed"].setText(_("%d kb/s") % (torrent.rateDownload / 1024))
			self["progress"].setValue(int(torrent.progress))

			status = torrent.status
			progressText = ''
			if status == 'check pending':
				peerText = _("check pending") # ???
			elif status == 'checking':
				peerText = _("checking")
				progressText = str(torrent.recheckProgress) # XXX: what is this? :D
			elif status == 'downloading':
				peerText = _("Downloading from %d of %d peers") % (torrent.peersSendingToUs, torrent.peersConnected)
				progressText = _("Downloaded %d of %d MB (%d%%)") % (torrent.downloadedEver/1048576, torrent.sizeWhenDone/1048576, torrent.progress)
			elif status == 'seeding':
				peerText = _("Seeding to %d of %d peers") % (torrent.peersGettingFromUs, torrent.peersConnected)
				progressText = _("Downloaded %d and uploaded %d MB") % (torrent.downloadedEver/1048576, torrent.uploadedEver/1048576)
			elif status == 'stopped':
				peerText = _("stopped")
				progressText = _("Downloaded %d and uploaded %d MB") % (torrent.downloadedEver/1048576, torrent.uploadedEver/1048576)
			self["peers"].setText(peerText)
			self["progress_text"].setText(progressText)
			self["ratio"].setText(_("Ratio: %.2f" % (torrent.ratio)))
			self["eta"].setText(_("Remaining: %s") % (torrent.eta or '?:??:??'))

			# XXX: we should not need to set this all the time but when we enter this screen we just don't have this piece of information
			trackers = torrent.trackers
			if trackers:
				self["tracker"].setText(_("Tracker: %s") % (trackers[0]['announce']))
			self["private"].setText(_("Private: %s") % (torrent.isPrivate and _("yes") or _("no")))

			l = []
			files = torrent.files()
			for id, x in files.iteritems():
				completed = x['completed']
				size = x['size'] or 1 # to avoid division by zero ;-)
				l.append((id, x['priority'], str(completed/1048576) + " MB", \
					x['selected'], x['name'], str(size/1048576) + " MB", \
					x['selected'] and _("downloading") or _("skipping"), \
					int(100*(completed / float(size)))
				))

			index = min(self["files"].index, len(l)-1)
			self["files"].setList(l)
			self["files"].index = index
		self.timer.startLongTimer(5)

	def ok(self):
		cur = self["files"].getCurrent()
		if cur:
			self.timer.stop()
			id = self.torrentid
			try:
				torrent = self.transmission.info([id])[id]
				files = torrent.files()

				# XXX: we need to make sure that at least one file is selected for
				# download so unfortunately we might have to check all files if
				# we are unselecting this one
				if cur[3]:
					files[cur[0]]['selected'] = False
					atLeastOneSelected = False
					for file in files.values():
						if file['selected']:
							atLeastOneSelected = True
							break
					if not atLeastOneSelected:
						self.session.open(
							MessageBox,
							_("Unselecting the only file scheduled for download is not possible through RPC."),
							type = MessageBox.TYPE_ERROR
						)
						self.updateList()
						return
				else:
					files[cur[0]]['selected'] = True

				self.transmission.set_files({self.torrentid: files})
			except transmission.TransmissionError:
				self.session.open(
					MessageBox,
					_("Could not connect to transmission-daemon!"),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)
			self.updateList()

	def close(self):
		self.timer.stop()
		Screen.close(self)

