from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, ServerFactory
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from Screens.InfoBar import InfoBar
from enigma import eServiceReference, eDVBVolumecontrol
from ServiceReference import ServiceReference

from Screens.MessageBox import MessageBox
from Tools import Notifications
from time import localtime, strftime
from os import uname

VERSION = '0.1'
SVDRP_TCP_PORT = 6419
NOTIFICATIONID = 'SVDRPNotification'

CODE_HELP = 214
CODE_EPG = 215
CODE_IMAGE = 216
CODE_HELO = 220
CODE_BYE = 221
CODE_OK = 250
CODE_EPG_START = 354 
CODE_ERR_LOCAL = 451
CODE_UNK = 500
CODE_SYNTAX = 501 
CODE_IMP_FUNC = 502
CODE_IMP_PARAM = 504
CODE_NOK = 550
CODE_ERR = 554
class SimpleVDRProtocol(LineReceiver):
	def __init__(self, client = False):
		self.client = client

	def connectionMade(self):
		self.factory.addClient(self)
		now = strftime('%a %b %d %H:%M:%S %Y', localtime())
		payload = "%d %s SVDRP VideoDiskRecorder (Enigma 2-Plugin %s); %s" % (CODE_HELO, uname()[1], VERSION, now)
		self.sendLine(payload)

	def connectionLost(self, reason):
		self.factory.removeClient(self)

	def stop(self, *args):
		payload = "%d %s closing connection" % (CODE_BYE, uname()[1])
		self.sendLine(payload)
		self.transport.loseConnection()

	def NOT_IMPLEMENTED(self, args):
		print "[SVDRP] command not implemented."
		payload = "%d command not implemented." % (CODE_IMP_FUNC,)
		self.sendLine(payload)

	def CHAN(self, args):
		# allowed parameters: [ + | - | <number> | <name> | <id> ]
		if args == '+':
			InfoBar.instance.zapDown()
			payload = "%d channel changed" % (CODE_OK,)
		elif args == '-':
			InfoBar.instance.zapUp()
			payload = "%d channel changed" % (CODE_OK,)
		else:
			# can be number, name or id
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)

		self.sendLine(payload)

	def LSTC(self, args):
		if args:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)
		from Components.Sources.ServiceList import ServiceList
		bouquet = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet')
		slist = ServiceList(bouquet, validate_commands=False)
		services = slist.getServicesAsList(format="SNn")
		if services:
			def sendServiceLine(service, last=False):
				if service[0][:5] == '1:64:':
					# format for markers:  ":Name"
					line = "%d%s:%s" % (CODE_OK, '-' if not last else ' ', service[1])
				else:
					# TODO: support full format, these are only the important fields ;)
					# <full name>,<short name>;<provider>:<freq>:(a lot more stuff o0)
					line = "%d%s%s,%s;UNK:" % (CODE_OK, '-' if not last else ' ', service[1], service[2])
				self.sendLine(line)
			lastItem = services.pop()
			for service in services:
				sendServiceLine(service)
			sendServiceLine(lastItem, last=True)
		else:
			payload = "%d no services found" % (CODE_ERR_LOCAL,)
			self.sendLine(payload)

	def LSTT(self, args):
		import NavigationInstance
		list = []
		recordTimer = NavigationInstance.instance.RecordTimer
		list.extend(recordTimer.timer_list)
		list.extend(recordTimer.processed_timers)
		list.sort(cmp = lambda x, y: x.begin < y.begin)

		def sendTimerLine(timer, counter, last=False):
			# <number> <flags>:<channel id>:<YYYY-MM-DD>:<HHMM>:<HHMM>:<priority>:<lifetime>:<name>:<auxiliary>
			flags = 0
			if not timer.disabled: flags |= 1
			if timer.state == timer.StateRunning: flags |= 8
			channelid = 1
			datestring = strftime('%Y-%m-%d', localtime(timer.begin))
			beginstring = strftime('%H%M', localtime(timer.begin))
			endstring = strftime('%H%M', localtime(timer.end))
			line = "%d%s%d %d:%d:%s:%s:%s:%d:%d:%s:%s" % (CODE_OK, '-' if not last else ' ', counter, flags, channelid, datestring, beginstring, endstring, 1, 1, timer.name, timer.description)
			self.sendLine(line)
		lastItem = list.pop()
		idx = 1
		for timer in list:
			sendTimerLine(timer, idx)
			idx += 1
		sendTimerLine(lastItem, idx, last=True)

	def MESG(self, data):
		if not data:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)

		Notifications.AddNotificationWithID(
			NOTIFICATIONID,
			MessageBox,
			text = data,
			type = MessageBox.TYPE_INFO,
			timeout = 5,
			close_on_any_key = True,
		)
		payload = "%d Message queued" % (CODE_OK,)
		self.sendLine(payload)

	def VOLU(self, args):
		volctrl = eDVBVolumecontrol.getInstance()
		if args == "mute":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volMute()
		elif args == "+":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volUp()
		elif args == "-":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volDown()
		elif args:
			try:
				num = int(args) / 2.55
			except ValueError:
				payload = "%d %s" % (CODE_SYNTAX, str(e).replace('\n', ' ').replace('\r', ''))
				return self.sendLine(payload)
			else:
				volctr.setVolume(num, num)

		if volctrl.isMuted():
			payload = "%d Audio is muted." % (CODE_OK,)
		else:
			payload = "%d Audio volume is %d." % (CODE_OK, volctrl.getVolume()*2.55)
		self.sendLine(payload)

	def lineReceived(self, data):
		if self.client or not self.transport or not data:
			return

		print "[SVDRP] incoming message:", data
		list = data.split(' ', 1)
		command = list.pop(0).upper()
		args = list[0] if list else ''

		"""
		CHAN      CLRE      DELC      DELR      DELT      
		EDIT      GRAB      HELP      HITK      LSTC      
		LSTE      LSTR      LSTT      MESG      MODC      
		MODT      MOVC      MOVT      NEWC      NEWT      
		NEXT      PLAY      PLUG      PUTE      REMO      
		SCAN      STAT      UPDT      VOLU      QUIT
		"""
		call = {
			'CHAN': self.CHAN,
			'LSTC': self.LSTC,
			'LSTT': self.LSTT,
			'QUIT': self.stop,
			'MESG': self.MESG,
			'VOLU': self.VOLU,
		}.get(command, self.NOT_IMPLEMENTED)

		try:
			call(args)
		except Exception, e:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			payload = "%d exception occured: %s" % (CODE_ERR, str(e).replace('\n', ' ').replace('\r', ''))
			self.sendLine(payload)

class SimpleVDRProtocolServerFactory(ServerFactory):
	protocol = SimpleVDRProtocol

	def __init__(self):
		self.clients = []

	def addClient(self, client):
		self.clients.append(client)

	def removeClient(self, client):
		self.clients.remove(client)

	def stopFactory(self):
		for client in self.clients:
			client.stop()

class SimpleVDRProtocolAbstraction:
	serverPort = None
	pending = 0

	def __init__(self):
		self.serverFactory = SimpleVDRProtocolServerFactory()
		self.serverPort = reactor.listenTCP(SVDRP_TCP_PORT, self.serverFactory)
		self.pending += 1

	def maybeClose(self, resOrFail, defer = None):
		self.pending -= 1
		if self.pending == 0:
			if defer:
				defer.callback(True)

	def stop(self):
		defer = Deferred()
		if self.serverPort:
			d = self.serverPort.stopListening()
			if d:
				d.addBoth(self.maybeClose, defer = defer)
			else:
				self.pending -= 1

		if self.pending == 0:
			reactor.callLater(1, defer.callback, True)
		return defer

