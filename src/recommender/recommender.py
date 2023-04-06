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
    
    def init_all_tag_relevances_dict(self):
        '''
        tag similarity describes the similarity of a course embedding to each of the tag embeddings of its respective subject
        '''
        tag_relevances_to_course = dict() # { subject : [relevance score] }
        for subject, tags_set in self.catalog.tags.items():
            tag_relevances_to_course.update({subject : np.zeros(len(tags_set))})
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

    def compute_tag_relevances_to_course(self, course:Course):
        '''
        returns:
            numpy array: contains the similarity score for the list of tags
        '''
        # fetching necessary attributes about this course
        subject = course.attr('subject')
        tags = self.catalog.tags.get(subject)
        if tags is None:
            return None
        
        # generation of relevance scores using embedding comparison
        tag_relevances_to_course = np.zeros(len(tags))

        for i in range(len(tags)):
            tag = tags[i]

            # accessing stored embedding caches
            # tag embeddings are stored inside the catalog
            tag_embedding = self.catalog.tag_embeddings.get(tag, None)
            if tag_embedding is None:
                tag_embedding = self.embed_message([tag])[0]
                self.catalog.tag_embeddings.update({tag:tag_embedding})

            # course embeddings are stored with each course
            course_embedding = course.embedding
            if course_embedding is None:
                course_embedding = self.embed_message([course.attr('name')])[0]
                course.embedding = course_embedding
            tag_relevances_to_course[i] = self.array_similarity(course_embedding, tag_embedding)

        # adjusts the score such that the best fit is much lower than all others
        smallest_num = min(tag_relevances_to_course)
        tag_relevances_to_course = np.add(tag_relevances_to_course, - (smallest_num - 0.01))

        # finds the best descriptors (for the sake of labelling)
        descriptors = dict(zip(self.catalog.tags.get(subject), tag_relevances_to_course))

        # sorted_descriptors = dictionary_sort(descriptors, True)
        sorted_descriptors = dictionary_sort(descriptors, True)[:3]
        best_descriptors = list()
        for tag, tag_relevance in sorted_descriptors:
            if tag_relevance < 0.11:
                best_descriptors.append(f'{tag} ({int(1 / tag_relevance)}%)')

        tag_relevances_to_course = self.hard_max(tag_relevances_to_course)
        course.tag_relevances = tag_relevances_to_course
        course.keywords = best_descriptors
        # print(f'COURSE FINAL {course} tags: {tags} relevance: {course_relevance_scores} tags: {best_descriptors}')

        return tag_relevances_to_course


    def embedded_relevance(self, taken_courses:set, recommending_courses:set) -> dict:
        all_course_relevances_to_user = dict()
        
        # sum of all similarities of a user's taken courses
        all_tag_relevances_to_user = self.init_all_tag_relevances_dict() # {subject : relevance array}

        # compute relevance of taken course and add to overall_relevances
        for course in taken_courses:
            subject = course.attr('subject')
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course, None)
            if tag_relevances_to_course is None:
                continue
            self.scale_dictionary_values(all_tag_relevances_to_user, tag_relevances_to_course, 1.0, key=subject)

        all_tag_relevances_to_user = {k: self.hard_max(v) for k, v in all_tag_relevances_to_user.items()} # normalization
        self.debug.print(f'overall relevances for each subject: {all_tag_relevances_to_user}')

        # compute relevance of each individual course and compare to overall_relevances based on course subject
        for course in recommending_courses:
            subject = course.attr('subject')
            tag_relevances_to_course = self.cache.tag_relevances_to_courses.get(course, None)
            if tag_relevances_to_course is None:
                all_course_relevances_to_user.update({course : 1})
                continue
            course_relevance_to_user = self.array_similarity(all_tag_relevances_to_user.get(subject), tag_relevances_to_course)
            all_course_relevances_to_user.update({course : course_relevance_to_user})

        sorted_course_relevances_to_user = dictionary_sort(all_course_relevances_to_user, True)

        self.debug.print('relevances by embedding: ' + str(['course: ' + str(c) + ' score: ' + str(s) + '\n' for c,s in sorted_course_relevances_to_user]))
        return all_course_relevances_to_user


    def embed_message(self, message):
        if not isinstance(message, list):
            message = [message]
        embedded_messages = self.embedder.embed(message)
        return embedded_messages
