import numpy as np

from .bag_of_words import *
from ..math.sorting import *
from ..recommender.embedding import Sentence_Embedder

class Recommender():

    def __init__(self, catalog):

        self.catalog = catalog
        self.dictionary = import_dictionary()
        self.embedder = Sentence_Embedder()

        self.embed_cache = dict()
        self.course_tags = dict() # tags of a course

    
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
    
    '''
    for numpy arrays
    '''
    def hard_max(self, x, adjust=1):
        sum = 0
        for i in range(0, len(x)):
            sum += np.exp(x[i]) - adjust
        for i in range(0, len(x)):
            x[i] = (np.exp(x[i]) - adjust ) / sum
        return x
    

    def loss(self, y:list, y_hat:list) -> float:
        sum = 0
        for i in range(0, len(y)):
            sum += np.absolute(y[i] - y_hat[i])
        return sum
    

    def smallest_k_num_pos(self, input_list, k):
        smallest_num_positions = []
        for iter_input in range(len(input_list)):
            if len(smallest_num_positions) < k:
                smallest_num_positions.append(iter_input)
                continue

            com_pos = iter_input
            for iter_tracker in range(len(smallest_num_positions)):
                # if we find a number that is better and tracking list is at capacity:
                if input_list[com_pos] < input_list[smallest_num_positions[iter_tracker]]:
                    old_pos = smallest_num_positions[iter_tracker]
                    smallest_num_positions[iter_tracker] = com_pos
                    com_pos = old_pos

        return smallest_num_positions


    def embedded_relevance(self, taken_courses:set, recommending_courses:set, reason:dict) -> dict:
        relevance = dict()
        
        # building relevance dictionary
        tag_relevances = self.generate_tag_relevances()

        for course in taken_courses:
            subject = course.attr('subject')
            tags = self.catalog.tags.get(subject)
            if tags is None:
                continue
            if self.embed_cache.get(course, None) is not None:
                relevance_list = self.embed_cache.get(course)
            else:
                relevance_list = np.zeros(len(tags))
                i = 0
                for tag in tags:
                    relevance_list[i] = self.embed_similarity(self.embed_message([course.attr('name')])[0], self.embed_message([tag])[0])
                    i += 1
                print(f'course pre softmax {course} tags: {tags} relevance: {relevance_list}')
                smallest_num = relevance_list[self.smallest_k_num_pos(relevance_list, 1)[0]]
                relevance_list = np.add(relevance_list, - (smallest_num - 0.01))
                print(f'course post adjustment {course} tags: {tags} relevance: {relevance_list}')
                best_descriptors = list()
                smallest_nums = self.smallest_k_num_pos(relevance_list, 2)
                for num in smallest_nums:
                    best_descriptors.append(tags[num])
                relevance_list = self.hard_max(relevance_list)
                self.embed_cache.update({course:relevance_list})
                self.course_tags.update({course : best_descriptors})
                print(f'COURSE FINAL {course} tags: {tags} relevance: {relevance_list} tags: {best_descriptors}')

            self.scale_relevances(tag_relevances, subject, relevance_list, 1.0)

        self.apply_to_all(tag_relevances, self.hard_max)

        for course in recommending_courses:
            subject = course.attr('subject')
            tags = self.catalog.tags.get(subject)
            if tags is None:
                relevance.update({course : -1})
                continue
            if self.embed_cache.get(course, None) is not None:
                relevance_list = self.embed_cache.get(course)
            else:
                relevance_list = np.zeros(len(tags))
                i = 0
                for tag in tags:
                    relevance_list[i] = self.embed_similarity(self.embed_message(course.attr('name'))[0], self.embed_message(tag)[0])
                    i += 1
                relevance_list = self.hard_max(relevance_list)
                self.embed_cache.update({course:relevance_list})
            
            loss = self.embed_similarity(tag_relevances.get(subject), relevance_list)

            relevance.update({course : loss})

        sorted_relevances = dictionary_sort(relevance, True)

        print('relevances by embedding: ' + str(['course: ' + str(c) + ' score: ' + str(s) + '\n' for c,s in sorted_relevances]))
        return relevance

    
    def embed_courses(self, courses:set):
        message = []
        for course in courses:
            message.append(course.attr('description') + ' ' + course.attr('name') + '. ')
        average_vector = np.average(self.embed_message(message))
        return average_vector


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

