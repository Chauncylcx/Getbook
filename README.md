# Getbook
这是一个简单的爬取小说的python程序

# 功能介绍
此程序首先会从代理IP网站获取可用代理IP地址，此后爬取所有的网页都会用代理IP来获取

第一步会爬取起点中文网收藏榜的书籍排名

第二步在书趣阁中搜索书籍信息，因为起点中文网需要VIP才能看书

第三步根据搜索到的书籍信息，通过多线程爬取书籍章节，因为多线程爬取章节顺序会乱，所以会先写到sqlite3数据库中

第四步将sqlite3中的章节按照编号重新写入txt文件，合成小说

