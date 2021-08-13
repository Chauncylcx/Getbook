# info: download books program
# author: Chauncy Liu
# date: 2021/08/05

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

	#获取可用代理IP并写入txt文件
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

	#get网页函数
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
				proxy_data = self.reget_ip()
				if attempts == 5:
					r = 1
					break
		return r
	
	#post网页函数
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
				proxy_data = self.reget_ip()
				if attempts == 5:
					r = 1
					break
		return r

	#初始化sqlite3数据表
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
		for i in range(1,2):
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
		burl = 'https://www.shuquge.com/search.php'
		for j in book_name:
			params = {'searchkey':j,'s':'6445266503022880974'}
			potxt = self.post_url(burl,params)
			if potxt == 1:
				print('爬取网页时出错，已跳过，链接为：{}'.fromat(url))
				continue
			potxt.encoding = 'UTF-8-SIG'
			soup = BeautifulSoup(potxt.text,'html.parser')	
			aobje = soup.find_all('div',class_='bookbox')
			num=0
			for li in aobje:
				if num >= 1:
					break
				a = li.find('a')
				templink=(a['href'])
				num+=1
			booklink[j] = 'https://www.shuquge.com' + templink
		print('从书趣阁搜索书名的链接地址完成...')
		return booklink

	#获取章节名称和章节链接
	def get_bookindex(self):
		booklink = self.post_bookname()
		print('开始爬取书籍章节...')
		apnum = 1
		for k,v in booklink.items():
			#控制爬取书籍的数量
			if apnum >= 3:
				continue
			pageinfo = []
			bobkindex = self.get_url(v)
			if bobkindex == 1:
				print('爬取网页时出错，已跳过，链接为：{}'.fromat(v))
				continue
			bobkindex.encoding = 'UTF-8-SIG'
			soup = BeautifulSoup(bobkindex.text,'html.parser')
			aobje = soup.find_all('dd')
			rlink = v.replace('index.html','')
			inde = 1
			for i in aobje:
				a = i.find('a')
				ilink = rlink + (a['href'])
				iname = "".join((a.string).split())
				pageinfo.append([ilink,iname,inde,k])
				inde+=1
			#使用队列为多线程服务
			q = queue.Queue()
			for i in pageinfo:
				q.put((i[0],i[1],i[2],i[3]))
			#设置5个线程
			thread_num = 5
			threads = []
			start = time.time()
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

	#获取章节内容
	def get_pageinfo(self,q):
		#开始获取章节内容
		while True:
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
				pagebook.encoding = 'UTF-8-SIG'
				soup = BeautifulSoup(pagebook.text,'html.parser')
				aobje = soup.find_all('div',class_='showtxt')
				aastr = str(aobje[0]).replace('<br/>','').replace('<div class="showtxt" id="content">','').replace(ilink,'').replace('请记住本书首发域名：www.shuquge.com。书趣阁_笔趣阁手机版阅读网址：m.shuquge.com','').replace('</div>','').replace('\xa0\xa0\xa0','\r\n').replace('\n','')
				sql = 'insert or ignore into bookinfo(bookname,bookid,booksub,booktext) values (\'%s\',\'%r\',\'%s\',\'%s\')'%(ibookname,inum,iname,aastr)
				retxt = self.post_db(sql)
				if retxt == 1:
					print('保存出错章节: ' + ibookname + iname)
				else:
					print('已保存章节：' + ibookname + iname)

def exp_db():
	#查询书名时去掉重复
	sql = 'select distinct bookname from bookinfo order by bookname,bookid'
	rebookname = openurl().get_db(sql)
	if rebookname == 1:
		print('导出数据时出错...')
		exit()
	for i in rebookname:
		sql = 'select bookname,booksub,booktext from bookinfo where bookname="%s" order by bookname,bookid'%i
		retxt = openurl().get_db(sql)
		bookname = str(retxt[0][0]) + '.txt'
		with open(bookname,'w',encoding='utf8') as f:
			for i in retxt:
				atite ='\r' +  i[1] + '\r'
				atext = i[2]
				f.write(atite)
				f.write(atext)

def main():
	inita = openurl()
	if os.path.exists('book.db'):
		os.remove('book.db')
	#检查数据库表是否存在
	sql = 'select count(*) from BOOKINFO'
	retxt = inita.get_db(sql)
	if retxt == 1:
		inita.init_db()
	#获取代理IP
	inita.get_proxyip()
	#开始爬取小说
	inita.get_bookindex()
	#导出数据生成txt文件
	exp_db()

if __name__ == '__main__':
	main()
