# -*- coding: utf-8 -*-

from Converter import Converter
from re import sub, split
from xml.dom.minidom import parseString as minidom_parseString

class WetterDotCom(Converter):
	"""Sample Parser which is able to parse Wetter.Com's website. Needs to have parse method which returns list of Forecasts."""
	def parse(self, data, type = "threeday"):
		# Filter whats non-forecast related
		#forecast = sub('<!-- FORECAST START -->(?P<forecast>.*?)<!-- FORECAST END -->', '\g<forecast>', data)
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

		# Unfortunately I'm unable to match this, although I don't know why
		# TODO: get a stable source for development ;)
		matches = split('<span class="Headline" style="line-height: 15px;">(.*?)</span>', data, 6)
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
