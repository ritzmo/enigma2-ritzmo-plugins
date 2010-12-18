DESCRIPTION = "Additional plugins for Enigma2"
MAINTAINER = "Moritz Venn <moritz.venn@freaque.net>"

SRCREV=""
SRCDATE="20101217"
BRANCH="master"
PV = "experimental-git${SRCDATE}"

PR = "r0"
SRC_URI="git://github.com/ritzmo/enigma2-ritzmo-plugins.git;protocol=git;branch=${BRANCH};tag=${SRCREV}"

DEPENDS = "enigma2"
# python-transmissionrpc is required for emission but I still keep the
# recipe to myself :-)

PACKAGE_ARCH = "all"

inherit autotools

S = "${WORKDIR}/git"

python populate_packages_prepend () {
	enigma2_plugindir = bb.data.expand('${libdir}/enigma2/python/Plugins', d)

	do_split_packages(d, enigma2_plugindir, '(.*?/.*?)/.*', 'enigma2-plugin-%s', 'Enigma2 Plugin: %s', recursive=True, match_path=True, prepend=True)

	def getControlLines(mydir, d, package):
		import os
		try:
			src = open(mydir + package + "/CONTROL/control").read()
		except IOError:
			return
		for line in src.split("\n"):
			if line.startswith('Package: '):
				full_package = line[9:]
			if line.startswith('Depends: '):
				depends = ' '.join(line[9:].split(', '))
				bb.data.setVar('RDEPENDS_' + full_package, depends, d)
			if line.startswith('Description: '):
				bb.data.setVar('DESCRIPTION_' + full_package, line[13:], d)

	mydir = bb.data.getVar('D', d, 1) + "/../git/"
	for package in bb.data.getVar('PACKAGES', d, 1).split():
		getControlLines(mydir, d, package.split('-')[-1])
}
