#
# A WIP TicTacToe-Implementation for the enigma2 gui
# Base code taken from: http://en.literateprograms.org/Tic_Tac_Toe_(Python)
#

# Plugin
from Plugins.Plugin import PluginDescriptor

#
from time import time
from random import shuffle

def allEqual(list):
	"""returns True if all the elements in a list are equal, or if the list is empty."""
	return reduce(lambda x, y: x and y, (x == list[0] for x in list), True)

Empty = ' '
Player_X = 'x'
Player_O = 'o'

class Board:
	"""This class represents a tic tac toe board state."""

	opponent = { Player_O: Player_X, Player_X: Player_O }

	def __init__(self):
		"""Initialize all members."""
		self.pieces = [Empty]*9
		self.field_names = '123456789'

	def winner(self):
		"""Determine if one player has won the game. Returns Player_X, Player_O or None"""
		winning_rows = [
			[0,1,2],[3,4,5],[6,7,8],	# vertical
			[0,3,6],[1,4,7],[2,5,8],	# horizontal
			[0,4,8],[2,4,6]				# diagonal
		]
		for row in winning_rows:
			if self.pieces[row[0]] != Empty and allEqual([self.pieces[i] for i in row]):
				return self.pieces[row[0]]

	def getValidMoves(self):
		"""Returns a list of valid moves. A move can be passed to getMoveName to 
		retrieve a human-readable name or to makeMove/undoMove to play it."""
		return [pos for pos in range(9) if self.pieces[pos] == Empty]

	def gameOver(self):
		"""Returns true if one player has won or if there are no valid moves left."""
		return self.winner() or not self.getValidMoves()

	def getMoveName(self, move):
		"""Returns a human-readable name for a move"""
		return self.field_names[move]
    
	def makeMove(self, move, player):
		"""Plays a move. Note: this doesn't check if the move is legal!"""
		self.pieces[move] = player
    
	def undoMove(self, move):
		"""Undoes a move/removes a piece of the board."""
		self.makeMove(move, Empty)

	# Evaluate a move based on resulting winner
	def evaluateMove(self, move, player, p, maxdepth, depth = 0):
		# Don't do anything when we reached maxdepth
		if maxdepth == depth:
			return 0

		try:
			# Make next move
			self.makeMove(move, p)

			# If game is over check who won
			if self.gameOver():
				winner = self.winner()
				if winner == player:
					return +1
				elif winner == None:
					return 0
				return -1

			# Evaluate next move
			outcomes = (self.evaluateMove(next_move, player, self.opponent[p], maxdepth, depth+1) for next_move in self.getValidMoves())

			# If player won
			if p == player:
				min_element = 1
				for o in outcomes:
					if o == -1:
						return o
					min_element = min(o,min_element)
				return min_element
			else:
				max_element = -1
				for o in outcomes:
					if o == +1:
						return o
					max_element = max(o,max_element)
				return max_element
		finally:
			self.undoMove(move)

	def computerPlayer(self, player, maxdepth = 1):
		"""Function for the computer player"""
		# Debug
		t0 = time()

		# List all possible moves
		moves = [(move, self.evaluateMove(move, player, player, maxdepth)) for move in self.getValidMoves()]

		# Shuffle this list to be a little random
		shuffle(moves)

		# Sort (player wins is better than no winner is better than oponent wins)
		moves.sort(key = lambda (move, winner): winner)

		# Some debug
		print "computer move: %0.3f ms" % ((time()-t0)*1000)
		print moves

		# Make this move
		self.makeMove(moves[-1][0], player)

# GUI (Components)
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText#MultiContentEntryPixmap
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT

class TicTacToeRow(GUIComponent):
	"""Defines a simple Component to convert human-readable cell content to pixmap"""
	def __init__(self, entries):
		GUIComponent.__init__(self)

		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(self.list)

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(25)

	def buildListboxEntry(self, content):
		res = [ None ]

		if content == Empty:
			png = ""
		elif content == Player_X:
			png = ""
		elif content == Player_O:
			png = ""
		else:
			print "INVALID BOARD"
			return res

		#res.append(MultiContentEntryPixmap(pos = (0, 0), size = (25, 25), png = png))
		res.append(MultiContentEntryText(pos=(0, 0), size=(25, 25), font=0, flags = RT_HALIGN_LEFT, text = content))

		return res

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def setList(self, l):
		return self.l.setList(l)

# GUI (Screen)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import NumberActionMap

class TicTacToe(Screen):
	"""Convert the board class into an enigma2 Screen"""

	skin = """<screen name="TicTacToe" position="150,150" size="100,100" title="TicTacToe">
			<widget name="firstRow" position="5,5" size="30,80" scrollbarMode="showNever" />
			<widget name="secondRow" position="35,5" size="30,80" scrollbarMode="showNever" />
			<widget name="thirdRow" position="65,5" size="30,80" scrollbarMode="showNever" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Initialize rows
		self["firstRow"] = TicTacToeRow([])
		self["secondRow"] = TicTacToeRow([])
		self["thirdRow"] = TicTacToeRow([])

		# Start a new game
		self.newGame(True)

		# ActionMap
		self["actions"] = NumberActionMap(["DirectionActions", "NumberActions", "OkCancelActions"],
			{
				"cancel": self.cancel,
				"ok": self.humanPlayer,
				"1": self.humanPlayer,
				"2": self.humanPlayer,
				"3": self.humanPlayer,
				"4": self.humanPlayer,
				"5": self.humanPlayer,
				"6": self.humanPlayer,
				"7": self.humanPlayer,
				"8": self.humanPlayer,
				"9": self.humanPlayer,
			}, -2
		)

	def cancel(self):
		self.session.openWithCallback(
			self.cancelCallback,
			MessageBox,
			"Do you really want to cancel?"
		)

	def cancelCallback(self, ret):
		if ret:
			self.close()

	def newGame(self, ret):
		"""begin a new game or close"""
		if ret:
			# Create new Board
			self.board = Board()

			# Reset turns
			self.turn = 1

			# Draw Board
			self.refreshBoard()

			# Player can move
			self.canMove = True
		else:
			self.close()

	def refreshBoard(self):
		"""Display the board on screen."""
		self["firstRow"].setList([
			(self.board.pieces[0],),
			(self.board.pieces[3],),
			(self.board.pieces[6],)
		])
		self["secondRow"].setList([
			(self.board.pieces[1],),
			(self.board.pieces[4],),
			(self.board.pieces[7],)
		])
		self["thirdRow"].setList([
			(self.board.pieces[2],),
			(self.board.pieces[5],),
			(self.board.pieces[8],)
		])

	def computerPlayer(self):
		"""The computer Player needs to move"""
		self.board.computerPlayer(Player_X, maxdepth = 3)
		self.refreshBoard()
		if self.board.gameOver():
			self.gameOver()
		else:
			self.turn += 1
			self.canMove = True

	def gameOver(self):
		"""Game is over"""

		# See if we have a winner
		winner = self.board.winner() 
		if winner:
			# Player won
			if winner == Player_O:
				message = _("You won!\nStart over?")
			# CPU won 
			else:
				message = _("You lost.\nStart over?")
		# Draw
		else:
			message = _("Draw.\nStart over?")

		# Show message
		self.session.openWithCallback(
			self.newGame,
			MessageBox,
			message
		)

	def humanPlayer(self, where = None):
		"""The human Player needs to move"""
		# Don't move when we're not supposed to
		if not self.canMove:
			return

		# Determine which cell is selected
		if where is None:
			# TODO: Determine which cell is selected
			return
		else:
			# We select using 1-9 but indexes are 0-8
			where -= 1

		# See if we actually can make this move
		if self.board.pieces[where] == Empty:
			self.canMove = False
			self.board.makeMove(where, Player_O)
			self.refreshBoard()
			if self.board.gameOver():
				self.gameOver()
			else:
				self.computerPlayer()

# Mainfunction
def main(session, **kwargs):
	session.open(TicTacToe)

# Plugin definitions
def Plugins(**kwargs):
	return [
			PluginDescriptor(name="Tic Tac Toe", description="Play a round of tic tac toe", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
	]
