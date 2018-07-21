import pickle
import os
from lxml import html
import requests
from multiprocessing.dummy import Pool as ThreadPool

class Website:
	
	INVALID_CHARACTER = list('\/:*?"<>| ')
	
	@classmethod
	def loadManga(cls):
		with open('{}.txt'.format(cls.name), 'rb') as f:
			return pickle.load(f)

	@classmethod
	def saveManga(cls, dictManga):
		with open('{}.txt'.format(cls.name), 'wb') as f:
			pickle.dump(dictManga, f)

	@classmethod
	def download(cls, path, url):
		response = requests.get(url)
		tree = html.fromstring(response.text)
		ls = tree.xpath(cls.imageXpath)
		title = tree.xpath(cls.titleCXpath)[0].text
		if cls.titleCSplit != None:
			title = title.split(cls.titleCSplit[0])[cls.titleCSplit[1]]
		image_urls = [x.attrib['src'] for x in ls]
		
		path = cls.createFolder(path, title)
		
		info =  [(path, i, image_urls[i]) for i in range(len(image_urls))]
		# Using ThreadPool to download faster
		pool = ThreadPool(4)
		pool.map(cls.saveImg, info)
		pool.close()
		pool.join()
		return path

	@staticmethod
	def saveImg(info):
		path, c, url = info
		with open(path + '\{0:02}.png'.format(c+1), 'wb') as f:
			f.write(requests.get(url).content)

	@staticmethod
	def filterFolderName(INVALID_CHARACTER, title):
		for char in INVALID_CHARACTER:
			title = title.replace(char, "_")
		return title.strip()

	@classmethod
	def createFolder(cls, path, title):
		title = cls.filterFolderName(cls.INVALID_CHARACTER, title)
		path += '\\' + title
		while os.path.exists(path):
			path += '_new'
		os.makedirs(path)
		return path

class hentaivn(Website):

	name = 'hentaivn'
	imageXpath = "//*[@id='image']/img"
	titleCXpath = "//head/title"
	titleCSplit = ("em Hentai Sex: ", 1)
	
	@classmethod
	def updateManga(cls):
		url = 'https://hentaivn.net/forum/search-plus.php?name=&dou=&char=&group=0&search=&page='
		a = requests.get(url + '1')
		tree = html.fromstring(a.text)
		ls = tree.xpath("//div//li/a")
		last_page = ls[-1].attrib['href'].split("page=")[-1]
		dictManga = {}
		for i in range(int(last_page)):
			print(i)
			page = requests.get(url + str(i + 1))
			tree = html.fromstring(page.text)
			for x in tree.xpath("//*[@class='search-des']/a"):
				if "the-loai" not in x.attrib["href"]:
					dictManga[x.text_content()] = 'https://hentaivn.net'\
					 + x.attrib['href']
		cls.saveManga(dictManga)

	@staticmethod
	def updateChapter(url):
		response = requests.get(url)
		tree = html.fromstring(response.text)
		ls_title = [i.attrib["title"].split("ruyện hentai ")[1] 
					for i in tree.xpath("//*[@class='chuong_t']")]
		ls_url = [i.attrib["href"] for i in tree.xpath("//td/a[@target='_blank']")]
		return {x[0]: 'https://hentaivn.net'\
				+ x[1] for x in zip(ls_title, ls_url)}

	@classmethod
	def prepareFolder(cls, path, url):
		response = requests.get(url)
		tree = html.fromstring(response.text)
		title = tree.xpath("//head//title")[0].text
		title = title.split("ruyện Hentai: ")[1]
		return cls.createFolder(path, title)

class blogtruyen(Website):
	
	name = 'blogtruyen'
	imageXpath = "//*[@id='content']/img"
	titleCXpath = "//header/h1"
	titleCSplit = None

	@classmethod
	def updateManga(cls):
		url = 'http://blogtruyen.com/timkiem/nangcao/1/0/-1/-1?p='
		a = requests.get(url + '1')
		tree = html.fromstring(a.text)
		idk = tree.xpath("//*[@title='Trang cuối']")
		last_page = idk[0].attrib['href'].split('=')[1]
		dictManga = {}
		for i in range(int(last_page)):
			page = requests.get(url + str(i + 1))
			tree = html.fromstring(page.text)
			for x in tree.xpath("//*[@class='fs-12 ellipsis tiptip']/a"):
				dictManga[x.text] = x.attrib['href']
		cls.saveManga(dictManga)

	@staticmethod
	def updateChapter(url):
		response = requests.get(url)
		tree = html.fromstring(response.text)
		ls = tree.xpath("//*[@id='list-chapters']//span[@class='title']/a")
		return {x.attrib['title']: 'http://blogtruyen.com'\
				+ x.attrib['href'] for x in ls}

	@classmethod
	def prepareFolder(cls, path, url):
		response = requests.get(url)
		tree = html.fromstring(response.text)
		title = tree.xpath("//head//title")[0].text
		title.split(" |")[0]
		return cls.createFolder(path, title)

