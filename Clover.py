from PyQt5 import QtCore, QtGui, QtWidgets
import image_rc
import webbrowser
import os
import pickle
import pyperclip
from SecondaryThread import updateThread, downloadThread
from classdata import Manga, Chapter, Container
from website import blogtruyen, hentaivn

# Status
INQUEUE = "In Queue"
COMPLETED = "Completed"
STOP = "Stop"
DOWNLOADING = "Downloading"
FAILED = "Failed"

chapter = "Chapter"
manga = "Manga"

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self):
		super().__init__()
		try:
			# Add stylesheet
			with open("defineQSS.txt", 'r') as f:
				keys = f.read().split("\n")
				dicts = {}
				for x in keys:
					delimiter = x.split(" = ")
					dicts[delimiter[0]] = delimiter[1]
				with open("style.qss", 'r') as g:
					data = g.read()
					for key in dicts:
						data = data.replace(key, dicts[key])
					self.setStyleSheet(data)
			# Read config
			with open("config.txt", "rb") as f:
				data = pickle.load(f)
			self.path = data["path"]
			self.minimize = data["minimize"]
			self.__version__ = data["version"]
			self.__author__ = data["author"]
			self.zip = data["zip"]

			if self.path == '':
				path = os.path.realpath(__file__)
				for x in path.split('\\')[:-1]:
					self.path += x + '\\'
				self.path = self.path[:-1]
			# Set up ui
		except:
			self.path = ''
			self.minimize = False
			self.__version__ = 1.0
			self.__author__ = "Thang Nguyen"
			self.zip = False
			self.Dialog("Some error happened when initialization!")

		self.initUi()
		self.show()

	def initUi(self):
		self.resize(1000, 500)
		self.widget = childWidget(self.path, self.zip)
		self.setCentralWidget(self.widget)

		# Menubar
		bar = self.menuBar()

		websiteMenu = bar.addMenu('Website')
		blogAction = self.createAction('Blogtruyen')
		blogAction.triggered.connect(lambda :self.widget.changeWebsite('blogtruyen'))
		henAction = self.createAction('Hentaivn')
		henAction.triggered.connect(lambda :self.widget.changeWebsite('hentaivn'))
		self.addActions(websiteMenu, [blogAction, henAction])

		settingMenu = bar.addMenu('Setting')
		settingAction = self.createAction('Config')
		settingAction.triggered.connect(self.settingDialog)
		updateAction = self.createAction('Update')
		updateAction.triggered.connect(self.widget.updateMangarequest)
		self.addActions(settingMenu, [settingAction, updateAction])

		helpMenu = bar.addMenu('Help')
		aboutAction = self.createAction('About')
		aboutAction.triggered.connect(self.aboutDialog)
		self.addActions(helpMenu, [aboutAction])

		# Task bar
		exit = QtWidgets.QAction("Exit", self)
		exit.triggered.connect(self.exitEvent)
		self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(':/icontaskbar.png'), self)
		menu = QtWidgets.QMenu(self)
		menu.addAction(exit)
		self.trayIcon.setContextMenu(menu)
		self.trayIcon.activated.connect(self.trayIconActivated)
		self.trayIcon.hide()
		self.setWindowIcon(QtGui.QIcon(':/icontaskbar.png'))

		self.setWindowTitle("Clover")

	def trayIconActivated(self, reason):
		if reason == QtWidgets.QSystemTrayIcon.Context:
			self.trayIcon.contextMenu().show()
		elif reason == QtWidgets.QSystemTrayIcon.Trigger:
			self.trayIcon.hide()
			self.show()
			self.raise_()

	def closeEvent(self, event):
		event.accept()
		if self.minimize:
			self.hide()
			self.trayIcon.show()
			event.setAccepted(True)
			event.ignore()
		elif self.minimize == None:
			event.accept()
		else:
			if self.widget.done:
				self.trayIcon.hide()
				del self.trayIcon
				event.accept()
			else:
				if self.warnMsgBox() == QtWidgets.QMessageBox.Yes:
					event.setAccepted(True)
					event.ignore()
				else:
					del self.trayIcon
					event.accept()
			
	def exitEvent(self):
		self.minimize = None
		self.close()

	def Dialog(self, msg):
		d = QtWidgets.QDialog(self)
		v = QtWidgets.QVBoxLayout()
		l = QtWidgets.QLabel(msg)
		v.addWidget(l)
		b = QtWidgets.QPushButton("Ok")
		b.clicked.connect(d.close)
		v.addWidget(b)
		d.setLayout(v)
		d.setWindowTitle("Warning")
		d.exec_()

	def aboutDialog(self):
		d = QtWidgets.QDialog(self)
		v = QtWidgets.QVBoxLayout()
		l = QtWidgets.QLabel("Version: {}".format(self.__version__))
		v.addWidget(l)
		l = QtWidgets.QLabel("Author: "+self.__author__)
		v.addWidget(l)
		d.setLayout(v)
		d.setWindowTitle("About")
		d.exec_()

	def warnMsgBox(self):
		d = QtWidgets.QMessageBox(self)
		d.setText("Queue is still downloading\nDo you want to stay?")
		d.setStandardButtons(QtWidgets.QMessageBox.Yes|
							QtWidgets.QMessageBox.No)
		d.setWindowTitle("Warning")
		return d.exec_()

	def settingDialog(self):
		d = QtWidgets.QDialog(self)
		v = QtWidgets.QVBoxLayout()
		self.c = QtWidgets.QCheckBox("Minimize to taskbar when I close")
		self.c.setChecked(self.minimize)
		v.addWidget(self.c)
		self.z = QtWidgets.QCheckBox("Create Zip for every chapter")
		self.z.setChecked(self.zip)
		v.addWidget(self.z)
		l = QtWidgets.QLabel("Download to:")
		v.addWidget(l)
		h = QtWidgets.QHBoxLayout()
		self.e = QtWidgets.QLineEdit()
		self.e.setObjectName("Directory")
		self.e.setText(self.path)
		self.e.setReadOnly(True)
		h.addWidget(self.e)
		b = QtWidgets.QPushButton()
		b.setObjectName('S')
		b.clicked.connect(self.getDirectory)
		self.pathget = self.path
		h.addWidget(b)
		h.addStretch()
		v.addLayout(h)
		b = QtWidgets.QPushButton("Save")
		b.clicked.connect(self.accepted)
		b.clicked.connect(d.close)
		v.addWidget(b)
		d.setLayout(v)
		d.setWindowTitle("Setting")
		d.exec_()

	def accepted(self):
		if self.pathget != "":
			self.path = self.pathget
			self.widget.path = self.pathget
		self.zip = self.z.isChecked()
		self.widget.zip = self.zip
		self.minimize = self.c.isChecked()
		try:
			with open("config.txt", 'wb') as f:
				pickle.dump({"path": self.path, "minimize": self.minimize,
							"version": self.__version__, "author": self.__author__,
							'zip': self.zip}, f)
		except AttributeError:
			self.Dialog("Could not open config.txt")

	def getDirectory(self):
		self.pathget = str(QtWidgets.QFileDialog.getExistingDirectory(\
							directory=self.path, caption="Select Directory"))
		if self.pathget != '':
			self.e.setText(self.pathget)

	def createAction(self, text, shortcut=None, icon=None):
		action = QtWidgets.QAction(text, self)
		if icon is not None:
			action.setIcon(QtGui.QIcon(":/{}.png".format(icon)))
		if shortcut is not None:
			action.setShortcut(shortcut)
		return action

	def addActions(self, target, actions):
		for action in actions:
			if action is not None:
				target.addAction(action)
			else:
				target.addSeparator()

class childWidget(QtWidgets.QWidget):
	# Add signal
	signalUpManga = QtCore.pyqtSignal(str)
	signalUpChap = QtCore.pyqtSignal(list)
	signalDownChap = QtCore.pyqtSignal(list)
	signalAddQueue = QtCore.pyqtSignal(list)

	def __init__(self, path, z):
		super().__init__()
		self.websites = {"blogtruyen": blogtruyen, 
						"hentaivn": hentaivn}
		self.dictChapter = {}
		self.web = "blogtruyen"
		self.path = path
		self.zip = z
		self.running = False
		self.chapboxWeb = self.web
		self.selected = []
		self.onQueue = None
		self.mangaPath = None
		self.webUpdate = None
		self.pivot = 0
		self.done = True

		self.initUi()

	def initUi(self):

		self.headerManga = QtWidgets.QHBoxLayout()

		self.searchBox = QtWidgets.QLineEdit(placeholderText='Press Enter to search')
		self.searchBox.setMaximumHeight(30)

		self.statusicon = QtWidgets.QLabel()
		self.statusicon.setObjectName(self.web)
		self.loadStyle()
		self.loading = QtGui.QMovie(':/loading.gif')
		self.loading.setScaledSize(QtCore.QSize(22, 22))
		self.loading.setSpeed(150)
		self.loading.start()

		self.headerManga.addWidget(self.statusicon)
		self.headerManga.addWidget(self.searchBox)

		self.mangaBox = QtWidgets.QListWidget()
		self.mangaBox.installEventFilter(self)
		
		self.topLeft = QtWidgets.QVBoxLayout()
		self.topLeft.addLayout(self.headerManga)
		self.topLeft.addWidget(self.mangaBox)

		self.chapterBox = QtWidgets.QListWidget()
		self.chapterBox.installEventFilter(self)
		self.chapterBox.setSelectionMode(\
			QtWidgets.QAbstractItemView.ExtendedSelection)

		self.top = QtWidgets.QHBoxLayout()
		self.top.addLayout(self.topLeft)
		self.top.addWidget(self.chapterBox)

		self.queueTable = QtWidgets.QTableWidget()
		self.queueTable.verticalHeader().hide()
		self.queueTable.installEventFilter(self)

		self.buttonGroup = QtWidgets.QHBoxLayout()
		self.start_btn = QtWidgets.QPushButton('Start Queue')
		self.stop_btn = QtWidgets.QPushButton('Stop Queue')
		self.start_btn.setMinimumWidth(60)

		self.buttonGroup.addWidget(self.start_btn)
		self.buttonGroup.addWidget(self.stop_btn)
		self.buttonGroup.addStretch()

		self.bottom = QtWidgets.QVBoxLayout()
		self.bottom.addLayout(self.buttonGroup)
		self.bottom.addWidget(self.queueTable)

		self.screen = QtWidgets.QVBoxLayout(self)
		self.screen.addLayout(self.top)
		self.screen.addLayout(self.bottom)
		font = QtGui.QFont()
		font.setFamily("Times New Roman")
		font.setPointSize(10)
		self.setFont(font)
		self.setLayout(self.screen)

		self.queueContainer = Container()
		self.chapMenu = QtWidgets.QMenu()
		self.addChapAction = self.createAction(text='Add to Queue')
		self.copyUrlAction = self.createAction(text='Copy URL')
		self.viewOnlineAction = self.createAction(text='View online')
		self.addChapAction.triggered.connect(self.addChapQueue)
		self.copyUrlAction.triggered.connect(self.copyUrl)
		self.viewOnlineAction.triggered.connect(self.openUrl)
		self.addActions(self.chapMenu, [self.addChapAction, \
			self.copyUrlAction, self.viewOnlineAction])

		self.mangaMenu = QtWidgets.QMenu()
		self.addMangaAction = self.createAction(text='Add to Queue')
		self.addMangaAction.triggered.connect(self.addMangaQueue)
		self.addActions(self.mangaMenu, [self.addMangaAction, \
			self.copyUrlAction, self.viewOnlineAction])

		self.queueMenu = QtWidgets.QMenu()
		self.queueRemove = self.createAction(text='Remove')
		self.queueRemove.triggered.connect(self.removeQueue)
		self.addActions(self.queueMenu, [self.queueRemove])

		# Event Handle
		self.mangaBox.itemDoubleClicked.connect(self.getChapterUrl)
		self.start_btn.clicked.connect(self.startQueue)
		self.stop_btn.clicked.connect(self.stopQueue)
		self.stop_btn.setEnabled(False)
		self.searchBox.returnPressed.connect(self.searchEngine)

		# Thread Handle
		self.threadGet = QtCore.QThread()
		self._threadGet = updateThread(chapterOut=self.updateChapter,\
										mangaOut=self.updateManga)
		self.signalUpChap.connect(self._threadGet.updateChapter)
		self.signalUpManga.connect(self._threadGet.updateManga)
		self._threadGet.moveToThread(self.threadGet)
		self.threadGet.start()

		self.threadDown = QtCore.QThread()
		self._threadDown = downloadThread(signalOut=self.doneQueue, \
											info=self.addQueueThread)
		self.signalDownChap.connect(self._threadDown.downChap)
		self.signalAddQueue.connect(self._threadDown.sendInfo)
		self._threadDown.moveToThread(self.threadDown)
		self.threadDown.start()

		self.refreshManga()
		self.updateQueue()

	def createAction(self, text, slot=None, shortcut=None,\
			icon=None):
			action = QtWidgets.QAction(text, self)
			if icon is not None:
				action.setIcon(QtGui.QIcon(":/{}.png".format(icon)))
			if shortcut is not None:
				action.setShortcut(shortcut)
			return action

	def addActions(self, target, actions):
		for action in actions:
			if action is not None:
				target.addAction(action)
			else:
				target.addSeparator()

	def eventFilter(self, source, event):
		if (event.type() == QtCore.QEvent.ContextMenu and
			source is self.chapterBox):
			self.selected = []
			for x in source.selectedItems():
				self.selected.append(x.text())
			self.chapMenu.exec_(event.globalPos())
			self.chapterBox.clearSelection()
		if (event.type() == QtCore.QEvent.ContextMenu and
			source is self.mangaBox):
			self.selected = []
			for x in source.selectedItems():
				self.selected.append(x.text())
			self.mangaMenu.exec_(event.globalPos())
			self.mangaBox.clearSelection()
		if (event.type() == QtCore.QEvent.ContextMenu and
			source is self.queueTable):
			self.queueMenu.exec_(event.globalPos())
			self.queueTable.clearSelection()

		return super().eventFilter(source, event)

	def dialog(self, msg, title="Warning"):
		d = QtWidgets.QDialog(self)
		v = QtWidgets.QVBoxLayout()
		l = QtWidgets.QLabel(msg)
		v.addWidget(l)
		b = QtWidgets.QPushButton("Ok")
		b.clicked.connect(d.close)
		v.addWidget(b)
		d.setLayout(v)
		d.setWindowTitle(title)
		d.exec_()
	
	def loadStyle(self):
		try:
			with open("styleStatus.qss", 'r') as g:
				data = g.read()
				self.setStyleSheet(data)
		except:
			self.dialog("Missing qss file")
			pass

	def changeWebsite(self, web):
		if self.web != web:
			self.web = web
			self.refreshManga()
			self.statusicon.setObjectName(self.web)
			self.loadStyle()

	def refreshManga(self):
		self.mangaBox.clear()
		self.dictManga = self.websites[self.web].loadManga()
		for manga in self.dictManga:
			self.mangaBox.addItem(manga)

	def updateMangarequest(self):
		self.signalUpManga.emit(self.web)
		self.webUpdate = self.web

	@QtCore.pyqtSlot(list)
	def updateManga(self):
		if package[0]:
			self.dialog(self.webUpdate + " have been updated!",\
						title="Message")
		else:
			self.catchError(package[1])

	def loadingProcess(self):
		self.statusicon.setMovie(self.loading)
		self.statusicon.setObjectName("loading")
		self.loadStyle()

	def loadingCompleted(self):
		m = QtGui.QMovie()
		self.statusicon.setMovie(m)
		self.statusicon.setObjectName(self.web)
		self.loadStyle()

	def getChapterUrl(self):
		self.chapterBox.clear()
		self.loadingProcess()
		for manga in self.mangaBox.selectedItems():
			mangaUrl = self.dictManga[manga.text()]
			self.signalUpChap.emit([self.web, mangaUrl])
		self.chapboxWeb = self.web

	@QtCore.pyqtSlot(list)
	def updateChapter(self, package):
		if package[0]:
			self.dictChapter = package[1]
			self.chapterBox.clear()
			for chapter in self.dictChapter:
				self.chapterBox.addItem(chapter)
		else:
			self.catchError(package[1])
		self.loadingCompleted()

	def addChapQueue(self):
		for x in self.selected:
			if x not in self.queueContainer:
				self.queueContainer.add(Chapter(x, INQUEUE, chapter,
									self.chapboxWeb, self.path, self.dictChapter[x]))
		self.updateQueue()

	def addMangaQueue(self):
		self.loadingProcess()
		self.signalAddQueue.emit([self.selected[0] ,self.web, self.path, \
								self.dictManga[self.selected[0]]])

	@QtCore.pyqtSlot(list)
	def addQueueThread(self, package):
		if package[0]:
			title, web, path, url, urls = package
			self.queueContainer.add(Manga(title, INQUEUE, manga, web, path, url, urls))
			self.updateQueue()
		else:
			self.catchError(package[1])
		self.loadingCompleted()

	def copyUrl(self):
		try:
			selectedUrl = [self.dictChapter[x] for x in self.selected]
			for url in selectedUrl:
				pyperclip.copy(url)
		except KeyError:
			selectedUrl = [self.dictManga[x] for x in self.selected]
			for url in selectedUrl:
				pyperclip.copy(url)

	def openUrl(self):
		try:
			selectedUrl = [self.dictChapter[x] for x in self.selected]
			for url in selectedUrl:
				webbrowser.open(url)
		except KeyError:
			selectedUrl = [self.dictManga[x] for x in self.selected]
			for url in selectedUrl:
				webbrowser.open(url)
			
	def searchEngine(self):
		text = self.searchBox.text()
		if str(text) != "":
			result = [x for x in self.dictManga if str(text).lower() in x.lower()]
			self.mangaBox.clear()
			for title in result:
				self.mangaBox.addItem(title)
		else:
			for manga in self.dictManga:
				self.mangaBox.addItem(manga)

	def startQueue(self):
		self.running = True
		self.emitSthIDK()
		self.updateQueue()

	def stopQueue(self):
		if self.onQueue is not None:
			if self.onQueue.type_ == manga:
				self.onQueue.status = STOP
		self.running = False
		self.start_btn.setEnabled(True)
		self.stop_btn.setEnabled(False)
		self.updateQueue()

	def conditionCheck(self):
		if not self.done:
			return False, None
		if not self.running:
			return False, None
		for item in self.queueContainer:
			if item.status == INQUEUE or \
				item.status == STOP or \
				item.status == FAILED or \
				"/" in item.status:
				return True, item
		return False, None

	def emitSthIDK(self):
		coutinue, item = self.conditionCheck()
		if coutinue:
			self.onQueue = item
			self.done = False
			if item.type_ == chapter:
				item.status = DOWNLOADING
				if self.zip:
					self.signalDownChap.emit([True, item.web, item.path, item.url])
				else:
					self.signalDownChap.emit([False, item.web, item.path, item.url])
			else:
				if self.pivot == 0:
					self.mangaPath = self.websites[item.web].prepareFolder(item.path, item.url)
				item.status = "{}/{}".format(self.pivot, len(item.urlChap))
				if self.zip:
					self.signalDownChap.emit([True, item.web, self.mangaPath, item.urlChap[self.pivot]])
				else:
					self.signalDownChap.emit([False, item.web, self.mangaPath, item.urlChap[self.pivot]])
			self.start_btn.setEnabled(False)
			self.stop_btn.setEnabled(True)
	
	def queueComplete(self):
		for item in self.queueContainer:
			if item.status != COMPLETED:
				return False
		return True

	def catchError(self, Num):
		if Num == 1:
			self.dialog("No connection is avaiable!")
		elif Num == 2:
			self.dialog("Address has error!")
		elif Num == 3:
			self.dialog("Could not find data in this address!")
		elif Num == 5:
			self.dialog("Connection is too slow to loadig!")
		elif Num == 6:
			self.dialog("Directory is not found")
		else:
			self.dialog("Something went wrong")

	@QtCore.pyqtSlot(int)
	def doneQueue(self, receive):
		if receive == 0:
			self.done = True
			if self.onQueue.type_ == chapter:
				self.onQueue.status = COMPLETED
			else:
				self.pivot += 1
				if self.pivot == len(self.onQueue.urlChap):
					self.pivot = 0
					self.onQueue.status = COMPLETED
			self.emitSthIDK()
			self.updateQueue()

			if self.queueComplete():
				self.running = False
				self.start_btn.setEnabled(True)
				self.stop_btn.setEnabled(False)
		else:
			self.catchError(receive)
			self.onQueue.status = FAILED
			self.pivot = 0
			self.onQueue = None
			self.done = True
			self.running = False
			self.start_btn.setEnabled(True)
			self.stop_btn.setEnabled(False)
			self.updateQueue()

	def removeQueue(self):
		indexes = self.queueTable.selectionModel().selectedRows()
		indexes.sort()
		indexes.reverse()
		for index in indexes:
			self.queueContainer.delete(index.row())
		self.updateQueue()

	def updateQueue(self, current=None):
		self.queueTable.setRowCount(self.queueContainer.length())
		self.queueTable.setColumnCount(5)
		self.queueTable.setHorizontalHeaderLabels(['Title',\
			 'Status', 'Type', 'Site', 'Save to'])
		self.queueTable.setAlternatingRowColors(True)
		self.queueTable.setEditTriggers(\
			QtWidgets.QTableWidget.NoEditTriggers)
		self.queueTable.setSelectionBehavior(\
			QtWidgets.QTableWidget.SelectRows)
		# self.queueTable.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
		self.queueTable.setSelectionMode(\
			QtWidgets.QTableWidget.ExtendedSelection)
		selected = None

		for row, manga in enumerate(self.queueContainer):
			item = QtWidgets.QTableWidgetItem(manga.title)
			if current is not None and current == id(manga):
				selected = item
			item.setData(QtCore.Qt.UserRole, \
				QtCore.QVariant(id(manga)))
			self.queueTable.setItem(row, 0, item)
			item = QtWidgets.QTableWidgetItem(manga.status)
			item.setTextAlignment(QtCore.Qt.AlignCenter)
			self.queueTable.setItem(row, 1, item)
			item = QtWidgets.QTableWidgetItem(manga.type_)
			item.setTextAlignment(QtCore.Qt.AlignCenter)
			self.queueTable.setItem(row, 2, item)
			item = QtWidgets.QTableWidgetItem(manga.web)
			item.setTextAlignment(QtCore.Qt.AlignCenter)
			self.queueTable.setItem(row, 3, item)
			item = QtWidgets.QTableWidgetItem(manga.path)
			self.queueTable.setItem(row, 4, item)

		header = self.queueTable.horizontalHeader()
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
		header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)

		if selected is not None:
			selected.setSelected(True)
			self.queueTable.setCurrentItem(selected)
			self.queueTable.scrollToItem(selected)

if __name__ == "__main__":
	import sys

	app = QtWidgets.QApplication(sys.argv)
	sd = MainWindow()
	sys.exit(app.exec_())