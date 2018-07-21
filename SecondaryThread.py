import requests
import shutil
from PyQt5 import QtCore
from website import blogtruyen, hentaivn

class Thread:
	def __init__(self):
		self.websites = {"blogtruyen": blogtruyen, 
						"hentaivn": hentaivn}

	def handleError(self, func, package):
		try:
			func(package)
		except requests.ConnectionError:
			self.chapterOut.emit([False, 1])
		except requests.Timeout:
			self.chapterOut.emit([False, 5])
		except requests.exceptions.HTTPError:
			self.chapterOut.emit([False, 2])
		except IndexError:
			self.chapterOut.emit([False, 3])
		except:
			self.chapterOut.emit([False, 4])

class updateThread(QtCore.QObject, Thread):
	"""
	Use Thread to prevent Gui breezing when
	get chapters	
	"""
	chapterOut = QtCore.pyqtSignal(list)
	mangaOut = QtCore.pyqtSignal(list)

	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)

	def handleChapter(self, package):
		website, url = package
		result = self.websites[website].updateChapter(url)
		self.chapterOut.emit([True, result])

	def handleManga(self, package):
		self.websites[package].updateManga()
		self.mangaOut.emit([True])

	@QtCore.pyqtSlot(list)
	def updateChapter(self, package):
		self.handleError(self.handleChapter, package)

	@QtCore.pyqtSlot(str)
	def updateManga(self, package):
		self.handleError(self.handleManga, package)

class downloadThread(QtCore.QObject, Thread):

	signalOut = QtCore.pyqtSignal(int)
	info = QtCore.pyqtSignal(list)

	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)

	def handleManga(self, package):
		title, website, path, url = package
		info = self.websites[website].updateChapter(url)
		urls = list(info.values())
		urls.reverse()
		self.info.emit([title, website, path, url, urls])
		
	@QtCore.pyqtSlot(list)
	def downChap(self, package):
		try:
			Zip, website, path, url = package
			path = self.websites[website].download(path, url)
			if Zip:
				shutil.make_archive(path, 'zip', path)
				shutil.rmtree(path, ignore_errors=True)
			self.signalOut.emit(0)
		except requests.ConnectionError:
			self.signalOut.emit(1)
		except requests.Timeout:
			self.signalOut.emit(5)
		except requests.exceptions.HTTPError:
			self.signalOut.emit(2)
		except IndexError:
			self.signalOut.emit(3)
		except FileNotFoundError:
			self.signalOut.emit(6)
		except:
			self.signalOut.emit(4)

	@QtCore.pyqtSlot(list)
	def sendInfo(self, package):
		self.handleError(self.handleManga, package)
