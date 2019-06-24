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
      
processed_count = 0
lock = threading.Lock()
write_lock = threading.Lock()
config_file = "config.yaml"


def if_deviceid_exist(map):
        if  "deviceId" in map and "deviceIdType" in map:
                return True
        return False

def extract_properties_from_header_map(map, key):
        return map[key]


def convert_context_headers_to_map(context_headers):
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

def curlComsByPurchaseOrderId(orderId):
        coms_url = "http://www.coms2.stratus.ebay.com/coms/lookupservice/v2/findPurchaseOrdersById"
        param = {
        "hints": [{}],
        "purchaseOrderId": [orderId]
        }
        content = proxyPost(coms_url, param)
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


def parse_sherlock_page(url):
      
        r = proxyGet(url.replace("\n",""), "")
        content = r.text
        m = re.search('.*var encoded_log_detail\= \"(.*)(\";\\r\\n\\t\\tvar log_detail.*)', content)
        raw_json = m.group(1).replace("\\", "")
        jsonO = json.loads(raw_json)
        jsonA = jsonO["calBlockResp"]
        return jsonA

def extractPurchaseOrderId(jsonA):
        calActivitesResp = jsonA[0]["calActivitesResp"]
        innerObj = calActivitesResp[len(calActivitesResp)-1]
        orderId = innerObj["data"]
        return orderId


def check_if_all_purchase_order_without_device_in_coms_response(x):
        jsonA = parse_sherlock_page(x)
        orderId = ""
        yml = load_config()
        if jsonA: 
                orderId = extractPurchaseOrderId(jsonA)
                if orderId and re.match('\d{14}', orderId): 
                        context_header = curlComsByPurchaseOrderId(orderId)
                        header_map = convert_context_headers_to_map(context_header)
                        if header_map and if_deviceid_exist(header_map):
                                write_purchase_order_without_device_in_coms_response(orderId)
                else:
                        logging.basicConfig(filename=yml["logging_file"], filemode='w', format='%(processName)s- %(threadName)s- %(levelname)s - %(message)s')
                        logging.warning("current page doesn't contain purchase order id or puchase order id format wrong. url=" + x)
        global processed_count            
        with lock:
                processed_count += 1
        print("processed_count={}".format(processed_count))


def proxyGet(url, param):
        yml = load_config()
        proxies = {"http":"http://zaniu:" + yml["yubikey"] + "@c2sproxy.vip.ebay.com:8080"}
        print("requests.get('{}',proxies={})".format(url, proxies))
        r = requests.get(url, proxies=proxies, params=param)
        return r


def proxyPost(url, param):
     
        yml = load_config()
        proxies = {"http":"http://zaniu:" + yml["yubikey"] + "@c2sproxy.vip.ebay.com:8080"}
        print("requests.post('{}',proxies={},json='{}')".format(url, proxies, param))
        r = requests.post(url, proxies=proxies, json=param)
        return r


def load_config():
        global config_file
        with open(config_file, 'r') as ymlfile:
                return yaml.load(ymlfile)


def count_no_deviceid_orders():
        yml = load_config()
        url_file = open(yml["url_file"], "r")
        executor = ThreadPoolExecutor(max_workers=10)
        for x in url_file:
                executor.submit(check_if_all_purchase_order_without_device_in_coms_response, x)

def write_purchase_order_without_device_in_coms_response(orderId):
        yml = load_config()
        with write_lock:
                found_in_coms_ids_f = open(yml["invalid_device_id_but_found_in_coms"], "w")
                found_in_coms_ids_f.write(orderId)
                found_in_coms_ids_f.close()


if __name__ == "__main__":
    count_no_deviceid_orders() 
