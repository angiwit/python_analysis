#!/usr/bin/env python

import json
import sys
import re
import requests
import time
import ast
import yaml
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

      

config_file = "config1.yaml"

class ExtractPurchaseOrderId(threading.Thread):
    
      def __init__(self, url=None):
            threading.Thread.__init__(self)
            self.count = 0
            self.errorCount = 0
            self.config = {}
            self.processed_count=0
            self.url = url
            

      def ifDeviceIdAbsent(self, map):
            if "deviceId" in map or "deviceIdType" in map:
                  return True
            return False

      def extract_properties_from_header_map(self, map, key):
            return map[key]
      

      def convert_context_headers_to_map(self, context_headers):
            temp_json = json.loads(context_headers)
            if "X-EBAY-C-ENDUSERCTX" in temp_json:
                  x_ebay_c_enduserctx = temp_json["X-EBAY-C-ENDUSERCTX"]
                  header_list = x_ebay_c_enduserctx.split(",")
                  header_map = {}
                  for _map in header_list:
                        row = _map.split("=")
                        header_map[row[0]] = row[1]
                  return header_map
            return

      def curlComsByPurchaseOrderId(self, orderId):
            coms_url = "http://www.coms2.stratus.ebay.com/coms/lookupservice/v2/findPurchaseOrdersById"
            param = {
                  "hints": [{}],
                  "purchaseOrderId": [orderId]
                }
            content = self.proxyPost(coms_url, param)
            text = content.text
            json_content = json.loads(text)
            PurchaseOrder = json_content["PurchaseOrder"]
            attributes = PurchaseOrder[0]["attributes"]
            for attribute in attributes:
                  if "name" in attribute and attribute["name"] == "CONTEXT_HEADERS":
                        content_headers = attribute["value"]
                  else:
                        continue
            return content_headers
      
      def new_yubikey(self):
            new_yubikey = input("please hit your yubikey:")
            print("new yubikey is: ", new_yubikey)
            with open("config.yaml", 'r') as ymlfile:
                  temp_config = yaml.load(ymlfile, Loader=yaml.FullLoader) or {}
                  temp_config["yubikey"] = new_yubikey
            with open("config.yaml", 'w') as ymlfile:
                  yaml.dump(temp_config, ymlfile)
            self.config["yubikey"]=new_yubikey
            return

      def parse_sherlock_page(self, url):
            r = self.proxyGet(url.replace("\n",""), "")
            content = r.text
            if r.status_code > 400:
                  return self.new_yubikey()
            else: 
                  m = re.search('.*var encoded_log_detail\= \"(.*)(\";\\r\\n\\t\\tvar log_detail.*)', content)
                  raw_json = m.group(1).replace("\\", "")
                  jsonO = json.loads(raw_json)
                  jsonA = jsonO["calBlockResp"]
                  return jsonA

      def extractPurchaseOrderId(self, jsonA):
            calActivitesResp = jsonA[0]["calActivitesResp"]
            innerObj = calActivitesResp[len(calActivitesResp)-1]
            orderId = innerObj["data"]
            return orderId

      def process(self, x):
            jsonA = self.parse_sherlock_page(x)
            orderId = ""
            yml = self.load_config()
            if jsonA: 
                  orderId = self.extractPurchaseOrderId(jsonA)
                  if orderId and re.match('\d{14}', orderId): 
                        context_header = self.curlComsByPurchaseOrderId(orderId)
                        header_map = self.convert_context_headers_to_map(context_header)
                        if header_map and self.ifDeviceIdAbsent(header_map):
                              found_in_coms_ids = open(yml["invalid_device_id_but_found_in_coms"], "w")
                              found_in_coms_ids.write(orderId + "\n")
                              found_in_coms_ids.close()
                              ##### when using print method make sure to use format method to print a string and the value you want to print, since only string type can be concated to a string.
                              # print("self.count={}".format(self.count))
                  else:
                        logging.basicConfig(filename=yml["logging_file"], filemode='w', format='%(processName)s- %(threadName)s- %(levelname)s - %(message)s')
                        logging.warning("current page doesn't contain purchase order id or puchase order id format wrong. url=" + x)
            else: 
                  ##### to handle the data without a json array blob.
                  return

      def proxyGet(self, url, param):
            yml = self.load_config()
            proxies = {"http":"http://zaniu:" + yml["yubikey"] + "@c2sproxy.vip.ebay.com:8080"}
            print("requests.get('{}',proxies={})".format(url, proxies))
            r = requests.get(url, proxies=proxies, params=param)
            return r


      def proxyPost(self, url, param):
            yml = self.load_config()
            proxies = {"http":"http://zaniu:" + yml["yubikey"] + "@c2sproxy.vip.ebay.com:8080"}
            print("requests.post('{}',proxies={},json='{}')".format(url, proxies, param))
            r = requests.post(url, proxies=proxies, json=param)
            return r

      def load_config(self):
            global config_file
            with open(config_file, 'r') as ymlfile:
                  return yaml.load(ymlfile)

      def count_no_deviceid_orders(self):
            yml = self.load_config()
            url_file = open(yml["url_file"], "r")
            executor = ThreadPoolExecutor(max_workers=10)

            for x in url_file:
                  executor.submit(self.process, x)

a = ExtractPurchaseOrderId()
a.count_no_deviceid_orders()