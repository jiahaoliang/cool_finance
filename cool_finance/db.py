from pymongo import MongoClient

from cool_finance import constants


class Client(object):

    def __init__(self, host=constants.DB_HOST, port=constants.DB_PORT):
        self.client = MongoClient(host, port)
        self.db = self.client[constants.DB_NAME]
        self.collection = self.db[constants.PRICE_COLLECTION]

    def insert_one(self, data_json, collection_name):
        if not collection_name:
            collection = self.collection
        else:
            collection = self.db[collection_name]
        id = collection.insert_one(data_json).inserted_id
        return id

