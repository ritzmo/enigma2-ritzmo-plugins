# -*- coding: utf-8 -*-

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
#from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
#from Components.config import config
from twisted.web.client import getPage
import re
from xml.dom.minidom import parseString as minidom_parseString
from urlparse import urlsplit

class WetterDotComParser:
	"""Sample Parser which is able to parse Wetter.Com's website. Needs to have parse method which returns list of Forecasts."""
	def parse(self, data, type = "threeday"):
		# Filter whats non-forecast related
		#forecast = re.sub('<!-- FORECAST START -->(?P<forecast>.*?)<!-- FORECAST END -->', '\g<forecast>', data)
		forecast = data

		# Split on row
		items = forecast.split('<td class="TAB_BOX_2_BODY_NOTBL" valign="bottom" align="right">')

		# TODO: needed?
		if type == "threeday":
			return [self.parseDay(items[i]) for i in range(1, 4)]
		elif type == "tenday":
			return [self.parseDay(items[i]) for i in range(1, 11)]

	def parseDay(self, data):
		"""Returns Weather-Information of a Day, here it is a 3-Tupel of (morning, noon, evening).
		   Other Parsers should return 4-Tupel of (desc., temp., precip., wind) if not as detailed
		   information is available."""
		matches = re.split('<span class="Headline" style="line-height: 15px;">(.*?)</span>', data, 6)
		return (
			self.parseElement(matches[1].split('<br>')),
			self.parseElement(matches[3].split('<br>')),
			self.parseElement(matches[5].split('<br>'))
		)

	def parseElement(self, data):
		"""Returns Weather-Element of a Day. 4-Tupel (description, temp, precip., wind)"""
		if len(data) == 2:
			return (
				data[0].strip().encode('UTF-8'),
				u"N/A",
				data[1].strip(),
				u"N/A"
			)
		return (
			data[0].strip().encode('UTF-8'),
			data[1].strip().replace('&deg;', u'°'),
			data[2].strip(),
			u"N/A"
		)

class ForecastScreen(Screen):

class WeatherScreen(Screen):
	skin = """<screen position="100,100" size="460,420" title="Weather Forecast" >
		<widget name="content" position="0,00" size="460,420" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, data):
		Screen.__init__(self, session)

		#self["contet"] = WeatherOverview(data)

		self["actions"] = ActionMap([ "OkCancelActions" ], 
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
		})

class WeatherForecast:
	availableParser = {
		"Wetter.com": WetterDotComParser
	}
	def __init__(self, session):
		self.session = session

	def error(self, errmsg = ""):
		self.session.open(MessageBox, "Error obtaining weather data", timeout = 5)
		print "[Weather] error occured: ", errmsg

	def gotPage(self, data):
		parser = WetterDotComParser()
		for day in parser.parse(data, "tenday"):
			if len(day) == 3:
				print "MORNING:", day[0]
				print "NOON:", day[1]
				print "EVENING:", day[2]
			else:
				print "ALLDAY:", day

	def showDialog(self):
		uri = "http://www.wetter.com/v2/?SID=&LANG=DE&LOC=7011&LOCFROM=0202&type=WORLD&id=19600"
		getPage(uri).addCallback(callback=self.gotPage).addErrback(self.error)

pluginInstance = None

def main(session, **kwargs):
	# Create Instance if none present, show Dialog afterwards
	global pluginInstance
	if pluginInstance is None:
		pluginInstance = WeatherForecast(session)
	pluginInstance.showDialog()

def Plugins(**kwargs):
	return [ PluginDescriptor(name="Weather Forecast", description="...", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main ) ]
