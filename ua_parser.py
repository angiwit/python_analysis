#!/bin/python

from ua_parser import user_agent_parser
import pprint
import json

def parse_ua():     
    pp = pprint.PrettyPrinter(indent=4)
    ua_string = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.104 Safari/537.36'
    parsed_string = user_agent_parser.Parse(ua_string)
    pp.pprint(parsed_string)

def parse_device_family():     
    # pp = pprint.PrettyPrinter(indent=4)
    with open("/Users/zaniu/Documents/logs/analysis/user_agent_file.txt", "r") as user_agent_file:
        user_agent_file_result = open("/Users/zaniu/Documents/logs/analysis/user_agent_file_result.txt", "w")
        for user_agent in user_agent_file:
            if user_agent: 
                parsed_string = user_agent_parser.ParseDevice(user_agent)
                if parsed_string: 
                    print("{}".format(parsed_string))
                    user_agent_file_result.write("{}".format(parsed_string) + "\n")
        user_agent_file_result.close

def parse_brand():     
    # pp = pprint.PrettyPrinter(indent=4)
    with open("/Users/zaniu/Documents/logs/analysis/user_agent_file.txt", "r") as user_agent_file:
        user_agent_file_result = open("/Users/zaniu/Documents/logs/analysis/user_agent_brand_result_os.txt", "w")
        for user_agent in user_agent_file:
            if user_agent: 
                parsed_map = user_agent_parser.ParseOS(user_agent)
                if parsed_map: 
                    print(parsed_map["family"])
                    user_agent_file_result.write("{}".format(parsed_map["family"]) + "\n")
        user_agent_file_result.close

def parse_single_brand():     
    pp = pprint.PrettyPrinter(indent=4)
    parsed_map = user_agent_parser.ParseOS("Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F74.0.3729.169+Safari%2F537.36")
    if parsed_map: 
        print(parsed_map["family"])
        

if __name__ == "__main__":
    parse_single_brand()