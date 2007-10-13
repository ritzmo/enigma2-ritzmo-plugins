from Components.VideoWindow import VideoWindow
from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference, eSize

from Screens.Screen import Screen

# Some target which is used nowhere else
UNUSED_TARGET = 1

# This is some kind of a modified PictureInPicture, unless we render in 0-size
class FakeTarget(Screen):
	skin = """<screen zPosition="-1" position="0,1" size="0,1" flags="wfNoBorder">
		<widget name="target" position="0,0" size="0,1" />
	</screen>
	"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self["target"] = VideoWindow(decoder = UNUSED_TARGET)
		self.onLayoutFinish.append(self.resize)

	def resize(self):
		self["target"].instance.resize(eSize(0, 1))

	# Modified Version of Screens.PictureInPicture.playService
	def playService(self, service):
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service

		if ref:
			# TODO: do we need to catch tune failed explicitly?
			self.epgservice = eServiceCenter.getInstance().play(ref)
			if self.epgservice and not self.epgservice.setTarget(UNUSED_TARGET):
				# DEBUG
				print "POLLING SERVICE", ref
				self.epgservice.start()

				# We were able to play service
				return True
			else:
				# DEBUG
				print "COULD NOT POLL SERVICE", ref

				# Destroy
				self.epgservice = None

		# Indicate that we need to skip this service
		return False

	def stop(self):
		self.epgservice = None