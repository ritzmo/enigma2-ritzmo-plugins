# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
#from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
#from Components.config import config
from twisted.web.client import getPage
from Tools.BoundFunction import boundFunction
from Converters.WetterDotCom import WetterDotCom

class WeatherScreen(Screen):
	skin = """<screen position="100,100" size="460,420" title="Weather Forecast" >
		<widget name="content" position="0,00" size="460,420" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, data):
		Screen.__init__(self, session)

		#self["content"] = WeatherOverview(data)

		self["actions"] = ActionMap([ "OkCancelActions" ], 
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
		})

class WeatherForecast:
	availableParser = {
		"Wetter.com": WetterDotCom
	}
	def __init__(self, session):
		# Save session locally to open Screens
		self.session = session

		# TODO: anything else to be done here?

	def error(self, errmsg = ""):
		self.session.open(MessageBox, "Error obtaining weather data", timeout = 5)
		print "[Weather] error occured: ", errmsg

	def gotPage(self, parser, data):
		# Instanciate correct parser and parse recieved data
		instance = parser()

		for day in instance.parse(data, "tenday"):
			if len(day) == 3:
				print "MORNING:", day[0]
				print "NOON:", day[1]
				print "EVENING:", day[2]
			else:
				print "ALLDAY:", day

		# TODO: open screen to show information

	def showDialog(self):
		# TODO: show dialog which enables you to select from a preconfigured source
		parser = "Wetter.com"
		uri = "http://www.wetter.com/v2/?SID=&LANG=DE&LOC=7011&LOCFROM=0202&type=WORLD&id=19600"
		if self.availableParser.has_key(parser):
			getPage(uri).addCallback(callback=boundFunction(self.gotPage, self.availableParser[parser])).addErrback(self.error)
		else:
			print "[Weather] Unknown Source!!!"

pluginInstance = None

def main(session, **kwargs):
	# Create Instance if none present, show Dialog afterwards
	# TODO: do we really need to keep this instance?
	global pluginInstance
	if pluginInstance is None:
		pluginInstance = WeatherForecast(session)
	pluginInstance.showDialog()

def Plugins(**kwargs):
	return [ PluginDescriptor(name="Weather Forecast", description="Fetch Weather forecasts from different sources", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main ) ]
