#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import datetime
import json
import os
import re
import requests
import urllib2
import ConfigParser


RATE_DATA_URL = "http://rate.bot.com.tw/Pages/Static/UIP003.zh-TW.htm"
TEMP_DIR = "/tmp"


def get_data():
    raising = None
    # Get last line of logfile
    # 讀取上次更新時間以及上次的現金賣出價格
    f = open(os.path.join(TEMP_DIR, 'jp_rate.log'), "r+")
    last_line = f.readlines()[-1]
    f.close()
    result = re.findall(r"\"(.*?)\", \"(.*?)\", \"(.*?)\", \"(.*?)\", \"(.*?)\"$", last_line)
    if result:
        print result[0][0]
        last_time_str = result[0][0]
        last_time = datetime.datetime.strptime(
            last_time_str,
            "%Y-%m-%d %H:%M:%S"
        )
        last_sell_price = float(result[0][2])
    else:
        last_time = datetime.datetime.strptime(
            "1970-01-01 00:00:00",
            "%Y-%m-%d %H:%M:%S"
        )
        last_sell_price = 0.0

    try:
        response = urllib2.urlopen(RATE_DATA_URL)
        page = response.read()
        rates = re.findall(r"JPY.+?([0-9]\.[0-9]+).+?([0-9]\.[0-9]+).+?([0-9]\.[0-9]+).+?([0-9]\.[0-9]+)", page)
        if rates[0][0] and rates[0][1] and rates[0][2] and rates[0][3]:
            rate_list = [
                rates[0][0],
                rates[0][1],
                rates[0][2],
                rates[0][3]
            ]
        if float(rates[0][1]) < last_sell_price:
            raising = False
        elif float(rates[0][1]) > last_sell_price:
            raising = True

        update_time_str = re.findall(r"([0-9]+/[0-9]+/[0-9]+\s[0-9][0-9]:[0-9][0-9])", page)

        if update_time_str[0]:
            update_time = datetime.datetime.strptime(
                update_time_str[0],
                "%Y/%m/%d %H:%M"
            )
            if update_time > last_time:
                # 寫入 log
                f = open(os.path.join(TEMP_DIR, 'jp_rate.log'), "a+")
                f.write('"%s", "%s", "%s", "%s", "%s"\n' % (
                    update_time,
                    rate_list[0],
                    rate_list[1],
                    rate_list[2],
                    rate_list[3]))
                f.close()

                data_dict = dict(
                    {
                        'update_time': update_time,
                        'rate_list': rate_list,
                        'raising': raising
                    }
                )
                return data_dict
            else:
                print "Not updated"
        else:
            return False
    except Exception as e:
        print e


def send_to_slack(data_dict, SLACK_WEBHOOK_URL):
    rate = data_dict['rate_list']
    if data_dict['raising'] is True:
        payload = {
            'text': ":arrow_upper_right: 日圓（JPY）：【現金匯率】（買入）%s, （賣出）%s 【即期匯率】（買入）%s, （賣出）%s（掛牌時間：%s）" % (rate[0], rate[1], rate[2], rate[3], data_dict['update_time']),
            'username': 'slack-rate-bot',
        }
    elif data_dict['raising'] is False:
        payload = {
            'text': ":arrow_lower_right: 日圓（JPY）：【現金匯率】（買入）%s, （賣出）%s 【即期匯率】（買入）%s, （賣出）%s（掛牌時間：%s）" % (rate[0], rate[1], rate[2], rate[3], data_dict['update_time']),
            'username': 'slack-rate-bot',
        }
    else:
        payload = {
            'text': ":arrow_right: 日圓（JPY）：【現金匯率】（買入）%s, （賣出）%s 【即期匯率】（買入）%s, （賣出）%s（掛牌時間：%s）" % (rate[0], rate[1], rate[2], rate[3], data_dict['update_time']),
            'username': 'slack-rate-bot',
        }

    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))


def config_reader(config_file_path):
    config = ConfigParser.ConfigParser()
    config.read(config_file_path)
    slack_webhook_url = config.get('global', 'SLACK_WEBHOOK_URL')
    return slack_webhook_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Config arguments for rate monitor"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="path of config file",
        required=True
    )
    args = parser.parse_args()

    SLACK_WEBHOOK_URL = config_reader(args.config)

    d = get_data()
    if (d):
        send_to_slack(d, SLACK_WEBHOOK_URL)
