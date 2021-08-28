# info: download books program
# author: Chauncy Liu
# date: 2021/08/05
# -*- coding: UTF-8 -*- 

import requests
import random
from bs4 import BeautifulSoup
import re
import time
import threading
from threading import Thread
from queue import Queue
import json
import os
import queue
import sqlite3

class openurl:
	#定义http头部，模拟浏览器访问
	def __init__(self):
		self.headers = [
			"Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
			"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
 			"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
			"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
			'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
			'Opera/9.25 (Windows NT 5.1; U; en)',
			'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
 			'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
			'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
			'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
			"Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
			"Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
        ]
	
	#随机生成一个http头部
	def get_random_header(self):
		randdom_agent = random.choice(self.headers)
		return randdom_agent

	#为了控制访问代理IP网站的频率，获取可用代理IP后写入txt文件,此后每次访问直接从本地文件随机抽取一个IP
	def get_proxyip(self):
		proxyip=[]
		url = 'https://ip.jiangxianli.com/api/proxy_ips'
		r = requests.get(url,params={'country':'中国'},headers={'User-Agent': self.get_random_header()},timeout=10)
		state = json.loads(r.text)
		with open('proxyip.txt','w') as f:
			for i in state['data']['data']:
				atext = str(i['protocol'] + '://' + i['ip'] + ':' + i['port'] + '\r')
				f.write(atext)
		print('代理IP爬取完成...')

	#读取txt文件并随机生成抽取一个代理地址
	def reget_ip(self):
		reip = []
		for line in open('proxyip.txt','r'):
			reip.append(line.replace('\n',''))
		randdom_ip = random.choice(reip)
		proiphttp = randdom_ip.split(':')[0]
		proxy_data={}
		proxy_data[proiphttp] = randdom_ip
		return proxy_data

	#get网页函数，若失败超过5次就退出
	def get_url(self,url):
		proxy_data = self.reget_ip()
		attempts = 0
		success = False
		while attempts < 5 and not success:
			try:
				r = requests.get(url,headers={'User-Agent': self.get_random_header()},proxies=proxy_data,timeout=5)
				success = True
			except:
				attempts += 1
				#访问时有可能是代理IP失效，失败后换一个代理IP试试
				proxy_data = self.reget_ip()
				if attempts == 5:
					r = 1
					break
		return r
	
	#post网页函数，若失败超过5次就退出
	def post_url(self,url,data):
		proxy_data = self.reget_ip()
		attempts = 0
		success = False
		while attempts < 5 and not success:
			try:
				r = requests.post(url,data=data,headers={'User-Agent': self.get_random_header()},proxies=proxy_data,timeout=5)
				success = True
			except:
				attempts += 1
				#访问时有可能是代理IP失效，失败后换一个代理IP试试
				proxy_data = self.reget_ip()
				if attempts == 5:
					r = 1
					break
		return r

	#初始化sqlite3数据表，主要临时存放书籍信息
	#随机ID，书籍章节序号，书名，书籍章节名，章节内容
	def init_db(self):
		try:
			conn = sqlite3.connect('book.db')
			c = conn.cursor()
			c.execute('''
				CREATE TABLE BOOKINFO (
				VID INTEGER PRIMARY KEY AUTOINCREMENT,
				BOOKID int NOT NULL,
				BOOKNAME TEXT NOT NULL,
				BOOKSUB TEXT NOT NULL,
				BOOKTEXT TEXT NOT NULL);
			''')
		except:
			print('数据库表创建失败，请检查')
		finally:
			conn.commit()
			conn.close()

	#查询数据
	def get_db(self,sql):
		try:
			conn = sqlite3.connect('book.db')
			c = conn.cursor()			
			cursor = c.execute(sql)
			res = cursor.fetchall()
		except sqlite3.OperationalError:
			return 1
		else:
			return res
		finally:
			conn.commit()
			conn.close()	

	#添加数据
	def post_db(self,sql):
		try:
			conn = sqlite3.connect('book.db')
			c = conn.cursor()
			c.execute(sql)
			conn.commit()
			conn.close()		
		except sqlite3.OperationalError:
			conn.close()
			return 1
		else:			
			return 0

	#从起点获取排行榜上的书名
	def get_bookname(self):
		bookname = []
		#控制爬取页面的数量，每页至少由10本小说，10页可查询排名前100的书籍
		for i in range(7,8):
			url = 'https://www.qidian.com/rank/collect/page{}/'.format(i)
			retxt = self.get_url(url)
			if retxt == 1:
				print('爬取网页时出错，已跳过，链接为：{}'.fromat(url))
				continue
			soup = BeautifulSoup(retxt.text,'html.parser')	
			aobje = soup.find_all('div',class_='book-mid-info')
			for li in aobje:
				a = li.find('a')
				bookname.append(a.string)
		print('起点排名爬取完成...')
		return bookname

	#从书趣阁搜索书名的链接地址
	def post_bookname(self):
		booklink = {}
		book_name = self.get_bookname()
		burl = 'https://www.biqooge.com/modules/article/search.php'
		for j in book_name:
			#搜索书籍用post方法，需要添加data参数，否则会搜索不到，通过F12查看
			params = {'searchkey':j.encode("gbk"),'searchtype':'articlename','action':'login','submit':j.encode("gbk")}
			potxt = self.post_url(burl,params)
			if potxt == 1:
				print('爬取网页时出错，已跳过，链接为：{}'.fromat(url))
				continue
			potxt.encoding = 'gbk'
			soup = BeautifulSoup(potxt.text,'html.parser')	
			titlename = soup.title.string
			if titlename.find('搜索') > 0:
				aobje = soup.find_all('td',class_='odd')
				for ai in aobje:
					a = ai.find('a')
					templink = (a['href'])
					booklink[j] = templink
					break
			else:
				templink = soup.find(attrs={"property":"og:novel:read_url"})['content']
				booklink[j] = templink
		print('书名地址搜索完成...')
		return booklink

	#获取章节名称和章节链接
	def get_bookindex(self):
		booklink = self.post_bookname()
		print('开始爬取书籍章节...')
		#检查数据库表是否存在，不存在就初始化数据库表
		if os.path.exists('book.db'):
			os.remove('book.db')
		sql = 'select count(*) from BOOKINFO'
		retxt = self.get_db(sql)
		if retxt == 1:
			self.init_db()
		apnum = 1
		#循环爬取每本书籍
		for k,v in booklink.items():
			#控制爬取书籍的数量，若不控制可去掉下面两行
			if apnum > 10:
				continue
			pageinfo = []
			bobkindex = self.get_url(v)
			if bobkindex == 1:
				print('爬取网页时出错，已跳过，链接为：{}'.fromat(v))
				continue
			bobkindex.encoding = 'gbk'
			soup = BeautifulSoup(bobkindex.text,'html.parser')
			aobje = soup.find_all('dd')
			rlink = 'https://www.biqooge.com'
			inde = 1
			#pageinfo保存每本书籍的章节名称、链接地址、章节编号、书名
			for i in aobje:
				a = i.find('a')
				ilink = rlink + (a['href'])
				iname = a.string
				#去掉前9章，后面才是正文
				if inde > 9:
					pageinfo.append([ilink,iname,inde,k])
				inde+=1

			#将pageinfo信息写入队列中
			q = queue.Queue()
			for i in pageinfo:
				q.put((i[0],i[1],i[2],i[3]))
			#设置5个线程
			thread_num = 5
			threads = []
			start = time.time()
			#如果章节为空则跳过此书籍
			if len(pageinfo) == 0:
				apnum+=1
				continue
			#将队列写入线程
			for i in range(len(pageinfo)):
				threads.append(
					threading.Thread(target=self.get_pageinfo,args=(q,))
				)

			#启动线程
			for i in range(thread_num):
				threads[i].start()
			#关闭线程
			for i in range(thread_num):
				threads[i].join()
			end = time.time()
			print(k,'爬取运行时间：',end-start,'秒')
			
			apnum+=1

			#爬取完一本书籍后生成一本完整的书籍
			sql = 'select bookname,booksub,booktext from bookinfo where bookname="%s" order by bookname,bookid'%k
			retxt = self.get_db(sql)
			bookname = str(retxt[0][0]) + '.txt'
			with open(bookname,'w',encoding='utf8') as f:
				for i in retxt:
					atite ='\r\n' + i[1] + '\r\n\n'
					atext = str(i[2]).replace('</div>','')
					f.write(atite)
					f.write(atext)

	#获取章节内容
	def get_pageinfo(self,q):
		#开始获取章节内容
		while True:
			#如果队列为空就退出
			if q.empty():
				return
			else:
				data = q.get()
				ilink = data[0]
				iname = data[1]
				inum = data[2]
				ibookname = data[3]
				pagebook = self.get_url(ilink)
				if pagebook == 1:
					print('爬取网页时出错，已跳过，链接为：{}'.fromat(ilink))
				pagebook.encoding = 'gbk'
				soup = BeautifulSoup(pagebook.text,'html.parser')
				aobje = soup.find_all('div',id='content')
				aastr = str(aobje[0]).replace('<br/>','').replace('<div id="content">','').replace('</div>','')				
				#将每个章节信息写入sqlite3数据库
				sql = 'insert or ignore into bookinfo(bookname,bookid,booksub,booktext) values (\'%s\',\'%r\',\'%s\',\'%s\')'%(ibookname,inum,iname,aastr)
				retxt = self.post_db(sql)
				if retxt == 1:
					print('保存出错章节: ' + ibookname + iname)
				else:
					print('已保存章节：' + ibookname + iname)

	#全部书籍爬取完成后再生成书籍
	#默认关闭，而是在每本书籍爬取后就生成
	def exp_db(self):
		#查询书名时去掉重复
		sql = 'select distinct bookname from bookinfo order by bookname,bookid'
		rebookname = self.get_db(sql)
		if rebookname == 1:
			print('导出数据时出错...')
			exit()
		for i in rebookname:
			sql = 'select bookname,booksub,booktext from bookinfo where bookname="%s" order by bookname,bookid'%i
			retxt = self.get_db(sql)
			bookname = str(retxt[0][0]) + '.txt'
			with open(bookname,'w',encoding='utf8') as f:
				for i in retxt:
					atite ='\r\n' + i[1] + '\r\n\n'
					atext = str(i[2]).replace('</div>','')
					f.write(atite)
					f.write(atext)

def main():
	inita = openurl()
	#获取代理IP
	#inita.get_proxyip()
	#开始爬取小说
	inita.get_bookindex()
	#导出数据生成txt文件
	#inita.exp_db()

if __name__ == '__main__':
	main()
