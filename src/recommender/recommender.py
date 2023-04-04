import numpy as np

from .bag_of_words import *
from ..math.sorting import *
from ..recommender.embedding import Sentence_Embedder

class Recommender():

    def __init__(self, catalog):

        self.catalog = catalog
        # self.dictionary = import_dictionary()
        self.embedder = Sentence_Embedder()

    
    def generate_tag_relevances(self):
        tag_relevances = dict() # { subject : [relevance score] }
        for subject, tags_set in self.catalog.tags.items():
            tag_relevances.update({subject : np.zeros(len(tags_set))})
        return tag_relevances
    
    
    def scale_relevances(self, tag_relevances, subject, additive, multiplicative):
        tag_relevances.update({subject : np.add(np.dot(tag_relevances.get(subject), multiplicative), additive)})


    def apply_to_all(self, tag_relevances, func):
        for key in tag_relevances.keys():
            tag_relevances.update({key : func(tag_relevances.get(key))})
    
    
    def embed_similarity(self, vec1, vec2):
        return np.linalg.norm(np.add(vec1, np.multiply(vec2, -1))).item()
    

    def soft_max(self, x):
        sum = 0
        for i in range(0, len(x)):
            sum += np.exp(x[i])
        for i in range(0, len(x)):
            x[i] = (np.exp(x[i])) / sum
        return x
    

    def hard_max(self, x, adjust=0.99):
        sum = 0
        for i in range(0, len(x)):
            sum += np.exp(x[i]) - adjust
        for i in range(0, len(x)):
            x[i] = (np.exp(x[i]) - adjust ) / sum
        return x
    

    def label_score_to_tag(self, subject, relevance) -> dict:
        labelled_dict = dict()

        i = 0
        for score in relevance:
            labelled_dict.update({self.catalog.tags.get(subject)[i] : score})
            i += 1

        return labelled_dict
    

    def get_course_relevances(self, course):
        # fetching necessary attributes about this course
        subject = course.attr('subject')
        tags = self.catalog.tags.get(subject)
        if tags is None:
            return None
        if course.embedding_relevance is not None and len(course.embedding_relevance):
            course_relevance_scores = course.embedding_relevance
        else:
            # generation of relevance scores using embedding comparison
            course_relevance_scores = np.zeros(len(tags))
            i = 0
            for tag in tags:
                course_relevance_scores[i] = self.embed_similarity(self.embed_message([course.attr('name')])[0], self.embed_message([tag])[0])
                i += 1

            # adjusts the score such that the best fit is much lower than all others
            smallest_num = min(course_relevance_scores)
            course_relevance_scores = np.add(course_relevance_scores, - (smallest_num - 0.01))

            # finds the best descriptors (for the sake of labelling)
            descriptors = self.label_score_to_tag(subject, course_relevance_scores)
            best_descriptors = dictionary_sort(descriptors, False)[:2]

            course_relevance_scores = self.hard_max(course_relevance_scores)
            course.embedding_relevance = course_relevance_scores
            course.keywords = best_descriptors
            # print(f'COURSE FINAL {course} tags: {tags} relevance: {course_relevance_scores} tags: {best_descriptors}')

        return course_relevance_scores


    def embedded_relevance(self, taken_courses:set, recommending_courses:set) -> dict:
        relevance = dict()
        
        # building relevance dictionary based on course subject
        overall_relevances = self.generate_tag_relevances() # {subject : relevance array}

        # compute relevance of taken course and add to overall_relevances
        for course in taken_courses:
            subject = course.attr('subject')
            course_relevance_scores = self.get_course_relevances(course)
            if course_relevance_scores is None:
                continue
            self.scale_relevances(overall_relevances, subject, course_relevance_scores, 1.0)

        self.apply_to_all(overall_relevances, self.hard_max) # normalization
        print(f'overall relevances after hard max: {overall_relevances}')

        # compute relevance of each individual course and compare to overall_relevances based on course subject
        for course in recommending_courses:
            subject = course.attr('subject')
            course_relevance_scores = self.get_course_relevances(course)
            if course_relevance_scores is None:
                relevance.update({course : -1})
                continue
            similarity = self.embed_similarity(overall_relevances.get(subject), course_relevance_scores)
            relevance.update({course : similarity})

        sorted_relevances = dictionary_sort(relevance, True)

        print('relevances by embedding: ' + str(['course: ' + str(c) + ' score: ' + str(s) + '\n' for c,s in sorted_relevances]))
        return relevance


    def embed_message(self, message):
        '''
        must be vector
        '''
        if not isinstance(message, list):
            message = [message]
        embedded_messages = self.embedder.embed(message)
        return embedded_messages


    def bag_of_words_relevance(self, taken_courses:set, recommending_courses:set, highly_matched_keywords:dict=None) -> dict:
        '''
        Algorithm:

        pre 1) generate a relations table of different words by reading academic articles
        pre 2) generate a list of keywords that are most important ranging across all subject areas

        1) for each course, compare it to each keyword and assign a degree of membership
        2) for courses the user has taken, calculate an average of degree of membership
        3) compare this average to all the courses being recommended using cross entropy and sort by highest similarity
        '''

        wanted_courses_keyword_values = dict()
        taken_courses_keyword_scores = dict()

        for taken_course in taken_courses:
            for keyword, keyword_count in get_keywords(taken_course.attr('description'), self.dictionary).items():
                taken_courses_keyword_scores.update({keyword : keyword_count + taken_courses_keyword_scores.get(keyword, 0)})

        for wanted_course in recommending_courses:

            highlighted_keywords = None
            if highly_matched_keywords is not None:
                highlighted_keywords = list()

            wanted_courses_keyword_values.update({wanted_course : self.bag_of_words_course_relevance(taken_courses_keyword_scores, wanted_course, highlighted_keywords)})
            
            if highly_matched_keywords is not None:
                highly_matched_keywords.update({wanted_course:highlighted_keywords})

        return wanted_courses_keyword_values
   

    def bag_of_words_course_relevance(self, taken_courses_keyword_scores:dict, wanted_course, highlighted_keywords:list=None) -> float:
        
        sum = 0.0
        keyword_ranking = dict()
        for course_keyword, course_keyword_count in get_keywords(wanted_course.attr('description'), self.dictionary).items():
            addition = taken_courses_keyword_scores.get(course_keyword, 0.0) * course_keyword_count
            sum += addition
            keyword_ranking.update({course_keyword:addition})

        if highlighted_keywords is not None:
            highlighted_keywords.extend(dictionary_sort(keyword_ranking))
        
        return sum
