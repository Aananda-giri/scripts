import os
import time
from pymongo.server_api import ServerApi

from dotenv import load_dotenv
load_dotenv()

# Creating mangodb
from pymongo import MongoClient

class Mongo():
    def __init__(self, db_name='scrapy-engine', collection_name="urls-collection", local=False):
        if local:
            client = MongoClient('localhost', 27017)
            self.db = client[db_name]
            self.collection = client[db_name][collection_name]
            
            # Ensure Index is Created for faster search operations
            self.collection.create_index('url', unique=True)
        else:
            
            uri = f"mongodb+srv://jokeleopedia:{os.environ.get('mongo_password')}@scrapy-engine.5cqch4y.mongodb.net/?retryWrites=true&w=majority&appName=scrapy-engine"
            # uri = f"mongodb+srv://{os.environ.get('mongo_username')}:{os.environ.get('mongo_password')}@scrapy-engine.xwugtdk.mongodb.net/?retryWrites=true&w=majority&appName=scrapy-engine"
            # uri = f"mongodb+srv://{os.environ.get('user_heroku')}:{os.environ.get('pass_heroku')}@cluster0.dgeujbs.mongodb.net/?retryWrites=true&w=majority"
            
            # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
            client = MongoClient(uri, server_api=ServerApi('1'))
            
            # Create the database for our example (we will use the same database throughout the tutorial
            self.db = client[db_name]
            self.collection = self.db[collection_name]  # using single collection for all urls
            # # one time operation
            # self.collection.create_index('url', unique=True)
    def check_connection(self):        
        # Create a new client and connect to the server
        uri = f"mongodb+srv://jokeleopedia:{os.environ.get('mongo_password')}@scrapy-engine.5cqch4y.mongodb.net/?retryWrites=true&w=majority&appName=scrapy-engine"
        client = MongoClient(uri, server_api=ServerApi('1'))
        # ping to confirm a successful connection
        try:
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)
    def append_url_crawled(self, url):
        try:
            # Try inserting url
            self.collection.insert_one({'url':url, 'timestamp':time.time(), 'status':'crawled'})
        except  Exception as ex:
            # url exists: change status to 'crawled'
            self.collection.update_one({'url':url}, {'$set': {'status':'crawled'}})
    def delete_to_crawl(self, url):
        try:
            self.collection.delete_one({'url':url, 'status':'to_crawl'})
        except Exception as ex:
            pass
            print(ex)
    def append_url_crawling(self, url):
        try:
            # Try inserting url
            self.collection.insert_one({'url':url, 'timestamp':time.time(), 'status':'crawling'})
            return True # inserted
        except  Exception as ex:
            # modify to_crawl to crawling
            result = self.collection.update_one(
                {'url': url, 'status': {'$in': ['to_crawl']}},
                {'$set': {'status':'crawling'}}, 
            )
            if result.modified_count > 0:
                # print("url was in to_crawl and now changed to crawling")
                return True
            else:
                # print("it is either already crawling or crawled")
                return False
    
    def append_url_to_crawl(self, url):
        if type(url) == list:
            # Insert multiple urls
            '''
            ordered=False: If an error occurs during the processing of one of the write operations, MongoDB will continue to process remaining write operations in the queue.
            '''
            try:
                self.collection.insert_many([{'url':u, 'timestamp':time.time(), 'status':'to_crawl?'} for u in url], ordered=False)
            except Exception as ex:
                pass
                # print(ex)
        elif type(url) == str:
            try:
                # Try inserting url
                self.collection.insert_one({'url':url, 'timestamp':time.time(), 'status':'to_crawl?'})
                return True # inserted
            except  Exception as ex:
                pass
                # print(ex)    # url exists

    def append_error_data(self, data):
        # Delete url if it's status is either 'to_crawl' or crawling
        # if status is crawled, try/except should avoid creating error url
        results = list(self.collection.find({'url':data['url'], 'status': {'$in': ['to_crawl', 'crawling']}}))
        if results:
            self.collection.delete_one({'_id':results[0]['_id']})

        try:
            # Try inserting url
            self.collection.insert_one(data)
            return True # inserted
        except  Exception as ex:
            print(ex)
            return   # error data exists

    def recover_expired_crawling(self, created_before=7200):
        # def convert_from_crawling_to_to_crawl(urls):
        #     # for url in urls:
        #     #     self.collection.update_one(
        #     #         {'_id':url['_id'], 'status': {'$in': ['crawling']}},
        #     #         {'$set': {'status':'to_crawl'}}
        #     #         )
        #     # perform bulk update
        #     if urls:
        #         self.collection.update_many(
        #             {'_id': {'$in': [url['_id'] for url in urls]}},
        #             {'$set': {'status':'to_crawl'}}
        #         )

        # get items with status 'crawling' and before timestamp 2 hours (7200)
        timestamp = time.time() - created_before  # 2 hours ago
        
        pipeline = [
            {"$match": {"status": "crawling", "timestamp": {"$lt": str(timestamp)}}},
            # {"$count": "count"}
        ]
        # The result is a list of documents returned by the aggregation pipeline
        expired_crawling_urls = list(self.collection.aggregate(pipeline))
        return expired_crawling_urls
        # convert_from_crawling_to_to_crawl(expired_crawling_urls)

    
    def fetch_start_urls(self, number_of_urls_required=10):
        # return [json.loads(url) for url in self.redis_client.srandmember('urls_to_crawl_cleaned_set', number_of_new_urls_required)]
        
        # Get all entries with  status 'to_crawl'
        random_urls = list(self.collection.aggregate([
            {"$match": {"status": "to_crawl"}},
            {"$sample": {"size": number_of_urls_required}}
        ]))
        # urls = list(self.collection.find({'status':'to_crawl'}).limit(number_of_urls_required))

        # perform bulk update
        if random_urls:
            self.collection.update_many(
                {'_id': {'$in': [url['_id'] for url in random_urls]}},
                {'$set': {'status':'crawling'}}
            )
        
        return random_urls
    def fetch_all(self):
        return list(self.collection.find())
    
    def set_configs(self, configs):
        '''
        # Tests:
            * variable types seems to be preserved
            * if key exists, value is updated otherwise new key-value pair is created
        # Format of configs
        ```
            configs = [
                {'crawl_other_data': False},
                {'crawl_paragraph_data':True},
                {'some_config':1000}
            ]
        ```
        '''

        for config in configs:
            self.db['config'].update_one(
                {'name': list(config.keys())[0]},
                {'$set': {'value': list(config.values())[0]}},
                upsert=True
            )
    def get_configs(self):
        '''
        # Returns data of format:
        ```
            {
                'crawl_other_data': False,
                'crawl_paragraph_data': True
            }
        ```
        '''
        configs_data = self.db['config'].find({})
        configs = {}
        for config in configs_data:
            configs[config['name']] = config['value']
        return configs

if __name__=="__main__":
    # delete all data and create unique index for field: 'url'
    mongo = Mongo()
    
    collection_names = ['url_crawled', 'url_to_crawl', 'url_crawling']
    for collection_name in collection_names:
        mongo.db_handler.delete_all(collection_name=collection_name)
        mongo.db_handler.db[collection_name].create_index('url', unique=True)