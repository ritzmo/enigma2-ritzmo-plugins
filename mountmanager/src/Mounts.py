from os import system, fork, _exit, waitpid, WNOHANG, kill, path
from enigma import eTimer
from xml.dom.minidom import parse as minidom_parse

XML_FSTAB = "/etc/enigma2/mounts.xml"

class Mounts():
	# Needed for fstab-handling
	identity = "# MountManager (don't edit anything below this line)"

	def __init__(self):
		# Read in XML when initing
		self.reload()

		# Initialize
		self.timer = None

	def getValue(self, definitions, default):
		# Initialize Output
		ret = ""

		# How many definitions are present
		Len = len(definitions)

		# We have definitions
		if Len > 0:
			# Iterate through nodes of last one
			for node in definitions[Len-1].childNodes:
				# Append text if we have a text node
				if node.nodeType == node.TEXT_NODE:
					ret = ret + node.data
		# If output is still empty return default
		if not len(ret):
			return default

		# Otherwise return output
		return ret

	def reload(self):
		# Initialize mounts to empty list
		self.mounts = []

		# Stop if no xml present
		if not path.exists(XML_FSTAB):
			return

		# Let minidom parse mounts.xml
		dom = minidom_parse(XML_FSTAB)

		# Config is stored in "mountmanager" element
		for config in dom.getElementsByTagName("mountmanager"):
			# Read out NFS Mounts
			for nfs in dom.getElementsByTagName("nfs"):
				for mount in nfs.getElementsByTagName("mount"):
					try:
						self.mounts.append(
							(
								"nfs",
								self.getValue(mount.getElementsByTagName("active"), "0"),
								self.getValue(mount.getElementsByTagName("ip"), "192.168.0.0"),
								self.getValue(mount.getElementsByTagName("share"), "/exports/"),
								self.getValue(mount.getElementsByTagName("dir"), "/media/net"),
								self.getValue(mount.getElementsByTagName("options"), "rw, nolock")
							)
						)
					except Exception, e:
						print "[MountManager] Error reading Mounts:", e

			# Read out CIFS Mounts
			for cifs in dom.getElementsByTagName("cifs"):
				for mount in cifs.getElementsByTagName("mount"):
					try:
						self.mounts.append(
							(
								"cifs",
								self.getValue(mount.getElementsByTagName("active"), "0"),
								self.getValue(mount.getElementsByTagName("ip"), "192.168.0.0"),
								self.getValue(mount.getElementsByTagName("share"), "/exports/"),
								self.getValue(mount.getElementsByTagName("dir"), "/media/net"),
								self.getValue(mount.getElementsByTagName("username"), "guest"),
								self.getValue(mount.getElementsByTagName("password"), "")
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
				list.append(''.join(["  <active>", mount[1], "</active>\n"]))
				list.append(''.join(["  <ip>", mount[2], "</ip>\n"]))
				list.append(''.join(["  <share>", mount[3], "</share>\n"]))
				list.append(''.join(["  <dir>", mount[4], "</dir>\n"]))
				list.append(''.join(["  <options>", mount[5], "</options>\n"]))
				list.append(' </mount>\n')
			list.append('</nfs>\n')

		# Same goes for CIFS
		if len(cifsmounts):
			list.append('<cifs>\n')
			for mount in cifsmounts:
				list.append(' <mount>\n')
				list.append(''.join(["  <active>", mount[1], "</active>\n"]))
				list.append(''.join(["  <ip>", mount[2], "</ip>\n"]))
				list.append(''.join(["  <share>", mount[3], "</share>\n"]))
				list.append(''.join(["  <dir>", mount[4], "</dir>\n"]))
				list.append(''.join(["  <username>", mount[5], "</username>\n"]))
				list.append(''.join(["  <password>", mount[6], "</password>\n"]))
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

	# TODO: deprecated
	def saveFstab(self):
		TMP_FSTAB = "/tmp/fstab"
		FSTAB = "/etc/fstab"

		file = None
		out = []
		move = True
		try:
			# Open System fstab
			file = open(FSTAB, "r")

			# Write everything from fstab into tempfile until identifier reached
			for line in file_in:
				if line.strip() == self.identity:
					break
				else:
					out.append(line)

			# Close file
			file.close()

			# Append identifier to outfile too
			out.append(self.identity)
			out.append('\n')

			# Now start appending mounts
			for mount in self.mounts:

				# Continue only if mountpoint active
				if mount[1] == "1":

					# Create valid syntax
					if mount[0] == "nfs":
						host = ':'.join([mount[2], mount[3]])
						options = mount[5]
					else:
						host = ''.join(["//", mount[2], "/", mount[3]])
						options = ''.join(["username=", mount[5], ",password=", mount[6]])

					out.append("%-30s %-15s %-5s %-15s 1 0\n" % (host, mount[4], mount[0], options))

			# Open temporary fstab and write it
			file = open(TMP_FSTAB, "w")
			file.writelines(out)
		except Exception, e:
			print "[MountManager] Error creating new Fstab:", e
			move = False
		finally:
			if file is not None:
				file.close()

		# We have to do this that way as files have to be closed first
		if move:
			# os.rename does not work ?!
			system(' '.join(["cp", TMP_FSTAB, FSTAB]))

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
					system("umount 2>/dev/null " + x[1])
		except:
			print "[MountManager] Error umounting"
		finally:
			if file is not None:
				file.close()

	def mount(self):
		# We force umount before mounting
		self.umount()

		# Initialize
		self.pids = []

		# TODO: Do we really want this to try/except ?
		try:
			for mount in self.mounts:
				# Continue if inactive
				if mount[1] == "0":
					continue

				# Make directory if subdir of /media
				if mount[4].startswith("/media/"):
					system(''.join(["mkdir -p ", mount[4]]))

				# Fork to not hang
				pid = fork()
				if pid == 0:
					print "Mounting:", mount[4]

					# Prepare Settings
					if mount[0] == "nfs":
						# Syntax: <ip>:<share>
						host = ':'.join([mount[2], mount[3]])
						options = ''
						split_options = mount[5].split(',')
						for option in split_options:
							options += ' '.join([" -o", option])
					else:
						# Syntax: //<ip>/<share>
						host = ''.join(["//", mount[2], "/", mount[3]])
						options = ''.join(["-o ", "username=", mount[5], " -o ", "password=", mount[6]])

					# Mount
					system(' '.join(["mount -t", mount[0], options, host, mount[4]]))
					_exit(0)
				else:
					self.pids.append(pid)
		except Exception, e:
			print "[MountManager] Error mounting:", e
		finally:
			# If we have processes running start a timer to take care of these
			if len(self.pids):
				self.timer = eTimer()
				self.timer.timeout.get().append(self.pidTimerFire)
				self.timer.startLongTimer(10)

	def pidTimerFire(self):
		# Walk through pids
		for process in self.pids:
			try:
				# Check if process is still running
				waitpid(process, WNOHANG)

				# When we reach this line the process is still running
				kill(process, 9)
			except:
				pass

		# Stop Timer
		self.timer.timeout.get().remove(self.pidTimerFire)
		self.timer = None

mounts = Mounts()
