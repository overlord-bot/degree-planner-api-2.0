import numpy as np

from ..math.sorting import *
from ..recommender.embedding import Sentence_Embedder
from ..io.output import *
from ..dp.course import Course
from ..recommender.cache import Cache

class Recommender():

    def __init__(self, catalog):

        self.catalog = catalog
        self.embedder = Sentence_Embedder() # embedder object to calculate embeddings
        self.cache = Cache()
        
        self.debug = Output(OUT.DEBUG, auto_clear=True)
        self.ATTRIBUTE_BIN = 'subject'
        self.ATTRIBUTE_TO_EMBED = 'name'

        self.reindex()

    def reindex(self):
        self.debug.print('initializing cache', OUT.INFO)

        self.cache.tag_embeddings.clear()
        self.cache.course_embeddings.clear()
        self.cache.tag_relevances_to_courses.clear()

        self.init_tag_embeddings()
        self.init_course_embeddings()
        self.init_tag_relevances_to_course()

        self.debug.print('finished initialization of cache', OUT.INFO)
    
    def init_tag_relevances_to_user(self):
        '''
        tag similarity describes the similarity of a course embedding to each of the tag embeddings of its respective bin
        '''
        tag_relevances_to_course = dict() # { bin : [relevance score] }
        for bin, tags_set in self.catalog.tags.items():
            tag_relevances_to_course.update({bin : np.zeros(len(tags_set))})
        return tag_relevances_to_course
    
    def scale_dictionary_values(self, dictionary, additive, multiplicative, key=None):
        if key is not None:
            dictionary.update({key : np.add(np.dot(dictionary.get(key), multiplicative), additive)})
            return
        for key in dictionary.keys():
            dictionary.update({key : np.add(np.dot(dictionary.get(key), multiplicative), additive)})
    
    def array_similarity(self, vec1, vec2):
        return np.linalg.norm(np.add(vec1, np.multiply(vec2, -1))).item()

    def soft_max(self, x):
        sum = 0
        for i in range(0, len(x)):
            sum += np.exp(x[i])
        for i in range(0, len(x)):
            x[i] = (np.exp(x[i])) / sum
        return x

    def hard_max(self, x, adjust=0.95):
        sum = 0
        for i in range(0, len(x)):
            sum += np.exp(x[i]) - adjust
        for i in range(0, len(x)):
            x[i] = (np.exp(x[i]) - adjust ) / sum
        return x
    
    def init_tag_embeddings(self, tags=None):
        '''
        can specify which tags to recompute, leave as None to recompute all
        '''
        # create list of tags
        if tags is None:
            tags = set()
            for tags_set in self.catalog.tags.values():
                for tag in tags_set:
                    tags.add(tag)
        # convert to set to ensure no duplicates
        elif not isinstance(tags, set):
            tags = set(tags)

        for tag in tags:
            tag_embedding = self.embed_message(tag)
            self.cache.tag_embeddings.update({tag:tag_embedding})


    def init_course_embeddings(self, course:Course=None):
        if course is None:
            for course in self.catalog.courses():
                self.init_course_embeddings(course)
            return
        
        course_embedding = self.embed_message(course.attr(self.ATTRIBUTE_TO_EMBED))
        self.cache.course_embeddings.update({course:course_embedding})


    def init_tag_relevances_to_course(self, course:Course=None):
        '''
        returns:
            numpy array: contains the similarity score for the list of tags
        '''
        if course is None:
            for course in self.catalog.courses():
                self.init_tag_relevances_to_course(course)
            return
        
        # fetching necessary attributes about this course
        bin = course.attr(self.ATTRIBUTE_BIN)
        tags = self.catalog.tags.get(bin)
        if tags is None:
            return
        
        # generation of relevance scores using embedding comparison
        tag_relevances_to_course = np.zeros(len(tags))

        # course embeddings are stored with each course
        course_embedding = self.cache.course_embeddings.get(course, None)
        if course_embedding is None:
            return

        for i in range(len(tags)):
            tag = tags[i]
            tag_embedding = self.cache.tag_embeddings.get(tag, None)
            if tag_embedding is None:
                return

            tag_relevances_to_course[i] = self.array_similarity(course_embedding, tag_embedding)

        # adjusts the score such that the best fit is much lower than all others
        smallest_num = min(tag_relevances_to_course)
        tag_relevances_to_course = np.add(tag_relevances_to_course, - (smallest_num - 0.01))

        # finds the best descriptors (for the sake of labelling)
        descriptors = dict(zip(self.catalog.tags.get(bin), tag_relevances_to_course))
        course.keywords = self.best_descriptors(descriptors, 3, 0.11)

        tag_relevances_to_course = self.hard_max(tag_relevances_to_course)
        self.cache.tag_relevances_to_courses.update({course:tag_relevances_to_course})

    
    def best_descriptors(self, descriptors, amount:int, threshold:float):
        sorted_descriptors = dictionary_sort(descriptors, True)[:amount]
        best_descriptors = list()
        for tag, tag_relevance in sorted_descriptors:
            if tag_relevance < threshold:
                best_descriptors.append(f'{tag} ({int(1 / tag_relevance)}%)')
        return best_descriptors


    def embedded_relevance(self, taken_courses:set, recommending_courses:set) -> dict:
        course_relevances_to_user = dict()
        
        # sum of all similarities of a user's taken courses
        tag_relevances_to_user_by_bin = self.init_tag_relevances_to_user() # {bin : relevance array}

        # compute a scaled sum of all of tag relevances of user's taken courses, organized by bin (such as course subject)
        for course in taken_courses:
            bin = course.attr(self.ATTRIBUTE_BIN)
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course, None)
            if tag_relevances_to_course is None:
                continue
            self.scale_dictionary_values(tag_relevances_to_user_by_bin, tag_relevances_to_course, 1.0, key=bin)

        tag_relevances_to_user_by_bin = {k: self.hard_max(v) for k, v in tag_relevances_to_user_by_bin.items()} # normalization
        self.debug.print(f'overall relevances for each subject: {tag_relevances_to_user_by_bin}')
        for bin, tags in self.catalog.tags.items():
            self.debug.print(f"user's best descriptors for {bin}: {self.best_descriptors(dict(zip(tags, tag_relevances_to_user_by_bin.get(bin))), 5, 0.3)}", OUT.INFO)

        # compute relevance of each recommending course and compare to user's tag relevances
        for course in recommending_courses:
            bin = course.attr(self.ATTRIBUTE_BIN)
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course, None)
            if tag_relevances_to_course is None:
                course_relevances_to_user.update({course : 1})
                continue
            course_relevance_to_user = self.array_similarity(tag_relevances_to_user_by_bin.get(bin), tag_relevances_to_course)
            course_relevances_to_user.update({course : course_relevance_to_user})

        sorted_course_relevances_to_user = dictionary_sort(course_relevances_to_user, True)

        self.debug.print('relevances by embedding: ' + str(['course: ' + str(c) + ' score: ' + str(s) + '\n' for c,s in sorted_course_relevances_to_user]))
        return course_relevances_to_user


    def embed_message(self, message):
        return_as_list = True
        if not isinstance(message, list):
            return_as_list = False
            message = [message]
        embedded_messages = self.embedder.embed(message)
        if return_as_list:
            return embedded_messages
        return embedded_messages[0]
    