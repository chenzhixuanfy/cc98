import requests
import re
import os
import sys
import time
import datetime
import threading
import random
import json


class cc98:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        self.auth_data = None# POST表单
        self.users = None# 用户
        self.latest_id = None# 最新的帖子id
        self.last_id = None# 上一次读过的帖子id
        self.URL = "https://api.cc98.org/Topic/{id}/post?from=0&size=1" # from是开始的楼数，size是返回总楼数（最多好像是20）
        self.URL_auth = "https://openid.cc98.org/connect/token"# 获取Authorization的地址
        self.URL_newTopics = "https://api.cc98.org/topic/new?from=0&size=1"# 获取最新的帖子
        self.timer = None# 别忘了定义
    
    
    # 获得Authorization，不知道client_id和client_secret多久更新一次
    def get_auth(self):
        self.write_log("Getting authorization...")
        response_auth = requests.post(self.URL_auth, data=self.auth_data, headers=self.headers)
        if(response_auth):
            auth_data = response_auth.json()
            self.headers["Authorization"] = auth_data["token_type"] + " " + auth_data["access_token"]
            self.write_log("Authorization is ready. ")
        else:
            self.write_log("Fail to get! ")
            time.sleep(5)
            self.get_auth()
    
    def get_method(self, URL, headers):
        response = requests.get(URL, headers = headers)
        self.write_log("status code = " + str(response.status_code))
        if(response.status_code != 200):# 授权过期
            self.get_auth()
        else:
            return response
    
    def get_latest_id(self):
        response = self.get_method(self.URL_newTopics, self.headers)
        data = response.json()
        self.latest_id = data[0]["id"]
        self.write_log("latest id: " + str(self.latest_id))
    
    # 写入日志并打印
    def write_log(self, text):
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")
        print(text)
    
    # 方糖消息推送
    def send_message_fangtang(self, SendKey, text, desp):
        data = {
            "text": text,
            "desp": desp# description，不是标题是内容
        }
        response = requests.post(f"https://sc.ftqq.com/{SendKey}.send", data=data)
        self.write_log(f"   方糖({SendKey}): {response.text}")
    
    # 匹配各个用户给关键词并发送
    def match_and_send(self, data):
        for user in self.users:
            for keyword in user["Keywords"]:
                matched = re.search(keyword, data[0]["title"] + "\n" + data[0]["content"], re.IGNORECASE)# re.IGNORECASE无视大小写
                if(matched):
                    send_text = data[0]["title"] + "\n" + "https://www.cc98.org/topic/" + str(data[0]["topicId"])
                    self.send_message_fangtang(user["SendKey"], "cc98", send_text)
                    break# 避免同一个用户匹配多次关键词多次消息推送
    
    # 爬虫程序
    def crawling(self):
        self.write_log(str(datetime.datetime.now()))
        try:
            self.get_latest_id()
        except Exception:
            except_type, except_value, except_traceback = sys.exc_info()
            except_file = os.path.split(except_traceback.tb_frame.f_code.co_filename)[1]
            exc_dict = {
                "报错类型": except_type,
                "报错信息": except_value,
                "报错文件": except_file,
                "报错行数": except_traceback.tb_lineno,
            }
            self.write_log(str(exc_dict))
            return

        for id in range(self.last_id, self.latest_id):
            response = self.get_method(self.URL.format(id=id+1), self.headers)
            try:
                data = response.json()
            except Exception:
                except_type, except_value, except_traceback = sys.exc_info()
                except_file = os.path.split(except_traceback.tb_frame.f_code.co_filename)[1]
                exc_dict = {
                    "报错类型": except_type,
                    "报错信息": except_value,
                    "报错文件": except_file,
                    "报错行数": except_traceback.tb_lineno,
                }
                self.write_log(str(exc_dict))
                continue

            self.write_log(data[0]["title"] + " " + "https://www.cc98.org/topic/" + str(data[0]["topicId"]))
            self.match_and_send(data)
            time.sleep(5)
        self.last_id = self.latest_id

        self.write_log("\n")

    # 定时执行（实际是隔随机时间执行）
    def func_timer(self):
        random_time = random.uniform(-60,60)# 小数的秒数，更不容易被发现
        
        self.crawling()

        # 定时器构造函数主要有2个参数，第一个参数为时间，第二个参数为函数名
        self.timer = threading.Timer(5*60+random_time, self.func_timer)   # 每过一段随机时间（单位：秒）调用一次函数

        self.timer.start()    #启用定时器

    # 初始化并开始爬虫   
    def crawler_start(self):
        # 新建log文件
        with open("log.txt", "w"):
            pass
        # 读取文件数据
        with open("auth_data.json", 'r') as f:
            self.auth_data = json.load(f)
        with open("user.json", 'r', encoding="utf-8") as f:
            self.users = json.load(f)
        
        self.write_log("Crawler starts...\n")

        self.get_auth()
        self.get_latest_id()
        self.last_id = self.latest_id - 5# 一开始先爬5个帖子
        self.timer = threading.Timer(1, self.func_timer)
        self.timer.start()

if __name__ == "__main__":
    cc98 = cc98()
    cc98.crawler_start()