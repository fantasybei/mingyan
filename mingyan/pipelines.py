# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import traceback

import pymongo
from pymongo.errors import DuplicateKeyError

from mingyan.MysqlUtil import MysqlUtil


class MingyanPipeline:
    __pool = None

    ershoufanglist = []
    global sql_insert
    sql_insert = " INSERT IGNORE INTO beike_ershoufang_wh (id, community_name, chengjiao_dealDate, chengjiao_totalPrice, chengjiao_unitPrice, xiaoqu_name, guapai_price, dealcycle_date, kanjia_price, area, house_age, city_name) " \
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "

    # sql_delete = """ DELETE FROM table_name WHERE id=%s """
    global sql_update
    sql_update = " UPDATE beike_ershoufang_wh SET area=%s,house_age=%s,chengjiao_unitPrice=%s WHERE id=%s "

    global sql_select
    sql_select = " SELECT COUNT(*) FROM beike_ershoufang_wh WHERE id=%s "

    def __init__(self):
        pass

    # 开启爬虫时链接数据库
    def open_spider(self, spider):
        self.__pool = MysqlUtil()

    def process_item(self, item, spider):
        try:

            params = (item['maidian_id'])
            count = self.__pool.get_one(sql=sql_select, param=params)
            self.__pool.end("commit")
            if count is not None and isinstance(count, tuple) and len(count) > 0 and count[0] > 0:
                print("------------------------------更新area" + str(item['maidian_id']))
                # params_update = (item['area'], item['house_age'], item['chengjiao_unitPrice'], item['maidian_id'])
                # self.__pool.update(sql=sql_update, param=params_update)
                # self.__pool.end("commit")

            else:
                print("------------------------------插入" + str(item['maidian_id']))
                self.ershoufanglist.append([item['maidian_id'],
                                            item['community_name'],
                                            item['chengjiao_dealDate'],
                                            item['chengjiao_totalPrice'],
                                            item['chengjiao_unitPrice'],
                                            item['xiaoqu_name'],
                                            item['guapai_price'],
                                            item['dealcycle_date'],
                                            item['kanjia_price'],
                                            item['area'],
                                            item['house_age'],
                                            item['city_name']])

                # 删除
                # params = {item['maidian_id']}
                # self.__pool.delete(sql_delete, params)
                # self.__pool.end("commit")

                if len(self.ershoufanglist) == 30:
                    self.__pool.insert_many(sql_insert, self.ershoufanglist)
                    self.__pool.end("commit")
                    # 清空缓冲区
                    del self.ershoufanglist[:]
        except Exception as e:
            logging.error('-----------------------------发生异常:[%s]', e)
            traceback.print_exc(e)
            self.__pool.end("rollback")
        return item

    # 关闭爬虫时执行，只执行一次。 (如果爬虫中间发生异常导致崩溃，close_spider可能也不会执行)
    def close_spider(self, spider):
        print("------------------------------closing spider,last commit", len(self.ershoufanglist))
        self.__pool.insert_many(sql_insert, self.ershoufanglist)
        self.__pool.end("commit")
        # 可以关闭数据库等
        self.__pool.dispose()
        pass


class MongoPipeline(object):
    collection_name = 'beike_ershoufang_chengjiao'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        data_dict = {'id': item['maidian_id'],
                     'community_name': item['community_name'],
                     'chengjiao_dealDate': item['chengjiao_dealDate'],
                     'chengjiao_totalPrice': item['chengjiao_totalPrice'],
                     'chengjiao_unitPrice': item['chengjiao_unitPrice'],
                     'xiaoqu_name': item['xiaoqu_name'],
                     'guapai_price': item['guapai_price'],
                     'dealcycle_date': item['dealcycle_date'],
                     'kanjia_price': str(item['kanjia_price']),
                     'area': item['area'],
                     'house_age': item['house_age'],
                     'city_name': item['city_name']}
        print("------------------------------mongo插入" + str(item['maidian_id']))
        self.db[self.collection_name].update(data_dict, {'$setOnInsert': data_dict}, upsert=True)
        return item
