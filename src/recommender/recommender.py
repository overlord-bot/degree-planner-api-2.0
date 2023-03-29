from ..io.relation_compute import *
from ..math.sorting import *

class Recommender():

    def __init__(self, catalog):

        self.catalog = catalog
        self.dictionary = import_dictionary()
        # graph = catalog_graph(catalog)
        # print(f'initialized course description graph: \n\n{graph} \n')

    def relevance(self, taken_courses:set, recommending_courses:set, highly_matched_keywords:dict=None) -> dict:
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

            wanted_courses_keyword_values.update({wanted_course : self.course_relevance(taken_courses_keyword_scores, wanted_course, highlighted_keywords)})
            
            if highly_matched_keywords is not None:
                highly_matched_keywords.update({wanted_course:highlighted_keywords})

        return wanted_courses_keyword_values
   

    def course_relevance(self, taken_courses_keyword_scores:dict, wanted_course, highlighted_keywords:list=None) -> float:
        
        sum = 0.0
        keyword_ranking = dict()
        for course_keyword, course_keyword_count in get_keywords(wanted_course.attr('description'), self.dictionary).items():
            addition = taken_courses_keyword_scores.get(course_keyword, 0.0) * course_keyword_count
            sum += addition
            keyword_ranking.update({course_keyword:addition})

        if highlighted_keywords is not None:
            highlighted_keywords.extend(dictionary_sort(keyword_ranking))
        
        return sum

