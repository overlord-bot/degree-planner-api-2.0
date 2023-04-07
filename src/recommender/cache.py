import json
import os
from ..io.output import *

class Cache():

    def __init__(self):
        self.CACHE_PATH = os.getcwd() + '/data/cache.json'

        self.course_embeddings = dict() # {course: embedding}
        self.tag_embeddings = dict() # {tag : embedding}
        self.tag_relevances_to_courses = dict() # relative distances to the embedding of all keywords within this courses's subject

        self.debug = Output(OUT.DEBUG, auto_clear=True)


    def read_cache(self):
    
        if os.path.isfile(self.CACHE_PATH):
            self.debug.print(f"file found: {self.CACHE_PATH}")
            file_embedding_cache = open(self.CACHE_PATH)
        else:
            self.debug.print("cache file not found")
            return
        
        json_data = json.load(file_embedding_cache)
        file_embedding_cache.close()

        for cache_category, cache in json_data.items():
            if not isinstance(cache, dict):
                self.debug.print('error: cache not a dictionary')
                continue
            if cache_category.casefold() == 'course_embeddings':
                self.course_embeddings = cache
            if cache_category.casefold() == 'tag_embeddings':
                self.tag_embeddings = cache
            if cache_category.casefold() == 'tag_relevances_to_courses':
                self.tag_relevances_to_courses = cache


    def store_cache(self):
        cache = dict()
        cache.update({'course_embeddings':self.course_embeddings})
        cache.update({'tags_embeddings':self.tag_embeddings})
        cache.update({'tag_relevances_to_courses':self.tag_relevances_to_courses})
        cache_json = json.dumps(cache)
        self.write_to_file(self.CACHE_PATH, cache_json)


    def clear(self):
        self.course_embeddings.clear()
        self.tag_embeddings.clear()
        self.tag_relevances_to_courses.clear()
        # self.write_to_file(self.CACHE_PATH, "")
        

    def write_to_file(self, file, text):
        if os.path.isfile(file):
            self.debug.print(f"file found: {file}")
        else:
            self.debug.print("file not found")
            return
        with open(file, "w") as output_file:
            output_file.write(text)
        output_file.close()
