import numpy as np

from ..math.sorting import *
from ..math.array_math import *
from ..io.output import *
from ..recommender.cache import Cache

class Recommender():

    def __init__(self, catalog, cache_path=None, enable_tensorflow=True):

        self.catalog = catalog
        self.cache = None
        self.scorer = None

        if enable_tensorflow:
            from ..recommender.scorer import Scorer
            self.scorer = Scorer(self.catalog, self.cache)

        self.ATTRIBUTE_BIN = 'subject'
        self.ATTRIBUTE_TO_EMBED = 'name'
        self.ENABLE_TENSORFLOW = enable_tensorflow
        self.CACHE_PATH = cache_path

        self.debug = Output(OUT.DEBUG, auto_clear=True)


    def get_scorer(self):
        if self.scorer is None:
            self.debug.warn("TENSORFLOW IS DISABLED")
        return self.scorer
    

    def create_cache(self):
        self.cache = Cache(self.CACHE_PATH)
    

    def load_cache(self):
        if self.cache is None:
            self.create_cache()
        self.debug.info("recommender loading cache")
        self.cache.load_cache()


    def reindex(self):
        scorer = self.get_scorer()
        if scorer is None:
            self.debug.warn("RECOMPUTE CACHE HALTED DUE TO TENSORFLOW DISABLED (no scorer found), NO CHANGES MADE")
            return
        if self.cache is None:
            self.create_cache()
        self.cache.clear()
        scorer.init_tag_relevances_to_courses()
        self.cache.store_cache()


    def get_custom_tag_relevances(self, course, custom_tags):
        scorer = self.get_scorer()
        if scorer is None:
            return np.zeros(len(custom_tags))
        return scorer.get_tag_relevances(course, custom_tags)


    def embedded_relevance(self, taken_courses:set, recommending_courses:set, custom_tags:set) -> dict:
        course_relevances_to_user = dict()
        
        ''' STEP 1: initialize dictionary of arrays that represent the relevance scores of each subject for the user '''
        tag_relevances_to_user_by_bin = dict() # { bin : [relevance score] }
        for bin, tags_set in self.catalog.tags.items():
            tag_relevances_to_user_by_bin.update({bin : np.zeros(len(tags_set))})

        ''' STEP 2: compute a scaled sum of all of tag relevances of user's taken courses, organized by bin (such as course subject) '''
        for course in taken_courses:
            bin = course.attr(self.ATTRIBUTE_BIN)
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course.unique_name, None)
            if tag_relevances_to_course is None:
                continue
            scale_dictionary_values(tag_relevances_to_user_by_bin, tag_relevances_to_course, 1.0, key=bin)

        ''' STEP 3: normalization '''
        tag_relevances_to_user_by_bin = {k: hard_max(v) for k, v in tag_relevances_to_user_by_bin.items()}

        # printing user's preference scores
        for bin, tags in self.catalog.tags.items():
            self.debug.print(f"user's best descriptors for {bin}: {best_descriptors(dict(zip(tags, tag_relevances_to_user_by_bin.get(bin))), 5, 0.3)}", OUT.INFO)

        ''' STEP 4: compute relevance of each recommending course and compare to user's tag relevances and relevance to the custom tag '''
        for course in recommending_courses:
            bin = course.attr(self.ATTRIBUTE_BIN)
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course.unique_name, None)
            course_relevance_to_user = 10
            if tag_relevances_to_course is not None:
                course_relevance_to_user = array_similarity(tag_relevances_to_user_by_bin.get(bin), tag_relevances_to_course)
            
            if custom_tags is not None and self.ENABLE_TENSORFLOW:
                custom_tag_relevances_to_course = self.get_custom_tag_relevances(course, custom_tags) # numpy array
                custom_course_relevance_to_user = array_similarity(custom_tag_relevances_to_course, np.zeros(len(custom_tag_relevances_to_course)))
                course_relevance_to_user += custom_course_relevance_to_user
            
            course_relevances_to_user.update({course : course_relevance_to_user})
            course.keywords = self.cache.course_keywords.get(course.unique_name)

        return course_relevances_to_user
    