# Create non-existant mountpoint
from os import makedirs, path

# Mount and check for hung processes
from enigma import eTimer, eConsoleAppContainer

# Parse config
from xml.etree.cElementTree import parse as cet_parse 

XML_FSTAB = "/etc/enigma2/mounts.xml"

class Mounts:
	"""Manages Mounts declared in a XML-Document."""
	def __init__(self):
		# Read in XML when initing
		self.reload()

		# Initialize Console
		self.callback = None
		self.run = -1
		self.commandSucceeded = True
		self.commands = [(None, "modprobe cifs")]
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.runFinished)
		self.container.dataAvail.append(self.dataAvail)

		# Initialize Timer
		self.timer = eTimer()
		self.timer.callback.append(self.mountTimeout)

		# Try to load cifs module (non-critical)
		self.nextCommand()

	def reload(self):
		# Initialize mounts to empty list
		self.mounts = []

		# Stop if no xml present
		if not path.exists(XML_FSTAB):
			return

		# Let minidom parse mounts.xml
		tree = cet_parse(XML_FSTAB).getroot()

		def getValue(definitions, default):
			# Initialize Output
			ret = ""

			# How many definitions are present
			Len = len(definitions)

			return Len > 0 and definitions[Len-1].text or default


		# Read out NFS Mounts
		for nfs in tree.findall("nfs"):
			for mount in nfs.findall("mount"):
				try:
					self.mounts.append(
						(
							"nfs",
							getValue(mount.findall("active"), "0"),
							getValue(mount.findall("ip"), "192.168.0.0"),
							getValue(mount.findall("share"), "/exports/"),
							getValue(mount.findall("dir"), "/media/net"),
							getValue(mount.findall("options"), "rw,nolock")
						)
					)
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e

		# Read out CIFS Mounts
		for cifs in tree.findall("cifs"):
			for mount in cifs.findall("mount"):
				try:
					self.mounts.append(
						(
							"cifs",
							getValue(mount.findall("active"), "0"),
							getValue(mount.findall("ip"), "192.168.0.0"),
							getValue(mount.findall("share"), "/exports/"),
							getValue(mount.findall("dir"), "/media/net"),
							getValue(mount.findall("username"), "guest"),
							getValue(mount.findall("password"), "")
						)
					)
				except Exception, e:
					print "[MountManager] Error reading Mounts:", e

	def getList(self):
		# Return List of Mountpoints
		return [x[4] for x in self.mounts]

	def getExtendedList(self):
		# Return List of 2-Tuples (mountpoint, active)
		return [(x[4], x[1]) for x in self.mounts]

	def getTuple(self, dir):
		# Search item, return it when found, return None otherwise
		if dir is not None:
			for mount in self.mounts:
				if mount[4] == dir:
					return mount
		return None

	def setTuple(self, dir, newtuple):
		# Search index, change tuples when found, append when not found
		assert(newtuple[0] in ["nfs", "cifs"])
		index = 0
		for mount in self.mounts:
			if mount[4] == dir:
				self.mounts[index] = newtuple
				return
			index += 1
		self.mounts.append(newtuple)

	def remove(self, dir):
		# Search index, pop it when found
		index = 0
		for mount in self.mounts:
			if mount[4] == dir:
				self.mounts.pop(index)
				return
			index += 1

	def save(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<mountmanager>\n']

		# Split up List of Mounts
		nfsmounts = []
		cifsmounts = []
		for mount in self.mounts:
			if mount[0] == "nfs":
				nfsmounts.append(mount)
			else:
				cifsmounts.append(mount)

		# Append NFS mounts if there are some
		if len(nfsmounts):
			list.append('<nfs>\n')
			for mount in nfsmounts:
				list.append(' <mount>\n')
				list.extend(["  <active>", mount[1], "</active>\n"])
				list.extend(["  <ip>", mount[2], "</ip>\n"])
				list.extend(["  <share>", mount[3], "</share>\n"])
				list.extend(["  <dir>", mount[4], "</dir>\n"])
				list.extend(["  <options>", mount[5], "</options>\n"])
				list.append(' </mount>\n')
			list.append('</nfs>\n')

		# Same goes for CIFS
		if len(cifsmounts):
			list.append('<cifs>\n')
			for mount in cifsmounts:
				list.append(' <mount>\n')
				list.extend(["  <active>", mount[1], "</active>\n"])
				list.extend(["  <ip>", mount[2], "</ip>\n"])
				list.extend(["  <share>", mount[3], "</share>\n"])
				list.extend(["  <dir>", mount[4], "</dir>\n"])
				list.extend(["  <username>", mount[5], "</username>\n"])
				list.extend(["  <password>", mount[6], "</password>\n"])
				list.append(' </mount>\n')
			list.append('</cifs>\n')

		# Close Mountmanager Tag
		list.append('</mountmanager>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_FSTAB, "w")
			file.writelines(list)
		except Exception, e:
			print "[MountManager] Error Saving Mounts List:", e
		finally:
			if file is not None:
				file.close()

	def singleUmount(self, dir):
		for mount in self.mounts:
			if mount[4] == dir:
				if self.container.execute('umount -f 2>/dev/null ' + dir):
					print "[MountManager] Umount of", dir, "failed!"

	def umount(self):
		# Only use active mountpoints
		mountpoints = [x[4] for x in self.mounts if x[1] == "1"]

		file = None
		try:
			# Read in Mounts
			file = open("/proc/mounts", "r")
			for line in file:
				x = line.split()

				# If Mountpoint is about to be mounted by us, umount
				if x[1] in mountpoints:
					self.container.execute('umount -f 2>/dev/null ' + x[1])
		except:
			print "[MountManager] Error umounting"
		finally:
			if file is not None:
				file.close()

	def mount(self, callback = None):
		# We force umount before mounting
		self.umount()

		# Initialize
		del self.commands[:]

		for mount in self.mounts:
			# Continue if inactive
			if mount[1] == "0":
				continue

			# Make directory if subdir of /media
			if mount[4].startswith("/media/"):
				try:
					makedirs(mount[4])
				except:
					pass

			# Prepare Settings
			if mount[0] == "nfs":
				# Syntax: <ip>:<share>
				host = ':'.join([mount[2], mount[3]])
				options = ''.join(['-o ', mount[5]])
			else:
				# Syntax: //<ip>/<share>
				host = ''.join(["//", mount[2], "/", mount[3]])
				options = ''.join(['-o ', 'username="', mount[5], '","password="', mount[6], '"'])

			# Our ready-to-go mount command
			cmd = ' '.join(["mount -t", mount[0], options, host, mount[4]]).encode("UTF-8")
			self.commands.append((mount[4], cmd))

		if len(self.commands):
			self.callback = callback
			self.run = -1
			self.nextCommand()

		# Return list of tuple (mountpoint, manual mount command)
		return self.commands

	def dataAvail(self, str):
		# Assume mount failed when mount outputs something
		self.commandSucceeded = False

	def runFinished(self, retval):
		self.timer.stop()
		if self.callback is not None:
			self.callback(self.commands[self.run][0], self.commandSucceeded)

		self.nextCommand()

	def nextCommand(self):
		self.run += 1
		if self.run < len(self.commands):
			self.timer.startLongTimer(10)
			self.commandSucceeded = True
			self.container.execute(self.commands[self.run][1])
		elif self.callback is not None:
			self.callback()

	def mountTimeout(self):
		self.container.kill()

		if self.callback is not None:
			self.callback(self.commands[self.run][0], False)
		
		self.nextCommand()

mounts = Mounts()
