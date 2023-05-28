# -*- coding: utf-8 -*-
import requests
import json
import pprint
import os
import csv


params = {
    "siteId": "3a2661c0628b4b7eb6123c7c5beb5d7a",
    "id": "1004009002",
    "languageType": "EN"
}

item_keys = ["year", "month", "OHC700-2000m(10^22J)"]
item_list = list()


def get_response(url="http://www.ocean.iap.ac.cn:8101/front//iap/datasetinfo/getTimeService"):
    proxy = {
        "https": "127.0.0.1:7890"
    }
    response = requests.get(url=url, params=params, proxies=proxy).text
    json_res = json.loads(response)
    pprint.pprint(json_res)
    data_list = json_res["data"][0]["data"]

    for data in data_list:
        item_values = [data[0].split(",")[0].split("/")[0], data[0].split(",")[0].split("/")[1], data[0].split(",")[1]]
        item = dict(zip(item_keys, item_values))
        item_list.append(item)
        print(item)


def save_csv():
    """
    save to csv file
    :return:
    """
    file_name = "OHC700-2000m.csv"

    print("数据保存.")
    for meta in item_list:
        with open(file_name, mode='a', encoding='utf-8', newline='') as f:
            csv_write = csv.DictWriter(f, fieldnames=item_keys)
            if os.path.getsize(file_name) == 0:
                csv_write.writeheader()

            csv_write.writerow(meta)
            f.close()


if __name__ == '__main__':
    get_response()
    save_csv()
