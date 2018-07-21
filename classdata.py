#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Chapter:

	def __init__(self, title, status, type_, web, located, url):
		self.title = title
		self.status = status
		self.type_ = type_
		self.web = web
		self.path = located
		self.url = url

class Manga:

	def __init__(self, title, status, type_, web, located, url, urlChap):
		self.title = title
		self.status = status
		self.type_ = type_
		self.web = web
		self.path = located
		self.url = url
		self.urlChap = urlChap

class Container:

	def __init__(self):
		self.__contain = []

	def add(self, manga):
		self.__contain.append(manga)
		
	def length(self):
		return len(self.__contain)

	def __iter__(self):
		for manga in self.__contain:
			yield manga

	def __contains__(self, title):
		for manga in self.__contain:
			if title == manga.title:
				return True
		return False

	def delete(self, index):
		del self.__contain[index]

	def __getitem__(self, index):
		return self.__contain[index]