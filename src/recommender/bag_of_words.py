'''
CURRENTLY PRETTY MUCH USELESS SO DON'T TOUCH
'''
import math
import re
from ..math.graph import Graph
from ..io.file_reader import *

NOUN = 'Noun'
VERB = 'Verb'
ADJ = 'Adjective'
ADV = 'Adverb'
ART = 'Article'

def catalog_graph(catalog):
    graph = Graph()
    dictionary = import_dictionary()

    for course in catalog:
        if course.attr('description') == None or course.attr('level') not in {'2', '4'} or course.attr('subject') == 'engr':
            continue
        print('course: ' + str(course))
        initialize_relations(course.name, course.attr('description'), graph, dictionary)
    return graph


def import_dictionary():
    nouns = import_csv_as_set(NOUNS_PATH)
    verbs = import_csv_as_set(VERBS_PATH)
    adjectives = import_csv_as_set(ADJECTIVES_PATH)
    adverbs = import_csv_as_set(ADVERBS_PATH)
    dictionary = {NOUN : nouns, VERB : verbs, ADJ : adjectives, ADV : adverbs}
    return dictionary


def get_keywords(text_body, dictionary) -> dict:
    if text_body is None:
        return {}
    text_body.replace('\r', '')
    text_body.replace('\n', '')

    words = text_body.split(' ')
    words.append('filler')
    words.insert(0, 'filler')
    seen_count = dict()

    if dictionary is None:
        print('WARNING, PRE-CREATE DICTIONARY TO MAXIMIZE PERFORMANCE!')
        nouns = import_csv_as_set(NOUNS_PATH)
        verbs = import_csv_as_set(VERBS_PATH)
        adjectives = import_csv_as_set(ADJECTIVES_PATH)
        adverbs = import_csv_as_set(ADVERBS_PATH)
        dictionary = {NOUN : nouns, VERB : verbs, ADJ : adjectives, ADV : adverbs}

    for cursor in range(1, len(words) - 1):
        word = words[cursor]
        if eligible_keyword(dictionary, word) and (keyword_indicator(dictionary, words[cursor - 1]) or keyword_indicator(dictionary, words[cursor + 1])):
            seen_count.update({word:seen_count.get(word, 0) + 1})

    return seen_count


def initialize_relations(text_title:str, text_body:str, graph:Graph=None, dictionary=None) -> Graph:
    '''
    takes in article title and body text

    Returns:
        graph: a relational graph of each keyword with each other
    '''
    if graph is None:
        graph = Graph()

    re.sub(r'\W+', '', text_body)
    
    text_body.replace('\r', '')
    text_body.replace('\n', '')

    title = text_title.split(' ')
    words = text_body.split(' ')
    words.extend(title)
    words.extend(title)
    words.append('filler')
    words.insert(0, 'filler')
    last_seen = dict()

    if dictionary is None:
        print('WARNING, PRE-CREATE DICTIONARY TO MAXIMIZE PERFORMANCE!')
        nouns = import_csv_as_set(NOUNS_PATH)
        verbs = import_csv_as_set(VERBS_PATH)
        adjectives = import_csv_as_set(ADJECTIVES_PATH)
        adverbs = import_csv_as_set(ADVERBS_PATH)
        dictionary = {NOUN : nouns, VERB : verbs, ADJ : adjectives, ADV : adverbs}

    for cursor in range(1, len(words) - 1):
        word = words[cursor]
        if eligible_keyword(dictionary, word) and (keyword_indicator(dictionary, words[cursor - 1]) or keyword_indicator(dictionary, words[cursor + 1])):
            last_seen.update({word : cursor})
            strengthen_word(graph, word, last_seen)

    for i in range(len(graph.grid)):
        hard_max(graph.grid[i])

    return graph


def eligible_keyword(dictionary, word:str) -> bool:
    if (word in {'a', 'an', 'it', 'so', 'well', 'in', 'out', 'as', 'can', 'since', 'this', 'course', 'class', 'is',
                'learn', 'about', 'teaches', 'the', 'using', 'are', 'and', 'or', 'not', 'because', 'be', 'study', 
                'studies', 'will', 'that', 'those', 'met', 'after', 'why', 'may', 'has', 'had', 'was', 'were', 'specific',
                'use', 'usage', 'show', 'how', 'which', 'why', 'by', 'along', 'do', 'does', 'make', 'did', 'made', 'look',
                'students', 'student', 'cover', 'review', 'at', 'goal', 'objective', 'observe', 'degree', 'required',
                'requirement', 'requires', 'offer', 'classes', 'offered', 'only'} 
            or word in dictionary.get(ADJ) or word in dictionary.get(ADV)):
        return False

    return word in dictionary.get(NOUN)


def keyword_indicator(dictionary, word:str) -> bool:
    if word in ('is', 'about', 'the', 'using', 'are'):
        return True

    return word in dictionary.get(NOUN) or word in dictionary.get(VERB)


def strengthen_word(graph:Graph, word:str, last_seen:dict) -> None:
    for other_word, last_occurance in last_seen.items():
        cursor = last_seen.get(word)
        multiplicative = 0.9
        additive = 1.0 - 1.1 * (sigmoid(cursor - last_occurance, 0.02) - 0.1)
        strengthen(graph, word, other_word, multiplicative, additive)


def strengthen(graph:Graph, element1, element2, multiplicative:float, additive:float):
    if element1 not in graph:
        graph.add_node(element1, True, 0)
    if element2 not in graph:
        graph.add_node(element2, True, 0)

    curr_num = graph.edge_data(element1, element2)
    if curr_num is None:
        curr_num = 0.01
    curr_num *= multiplicative
    curr_num += additive

    graph.update_connection(element1, element2, curr_num)
    graph.update_connection(element2, element1, curr_num)


def scale(graph:Graph, multiplicative, additive, limit_to=None):
    for n1, n2, num in graph.edge_items():
        if limit_to is not None and (n1 not in limit_to or n2 not in limit_to):
            continue
        num *= multiplicative
        num += additive
        graph.update_connection(n1, n2, num)


def sigmoid(num, multi=1.0, add=0.0):
    return 1 / (1 + math.exp(-(num * multi + add)))


def hard_max(x:list):
    sum = 0.0
    for i in range(0, len(x)):
        if x[i] is None:
            continue
        sum += (math.exp(x[i]) - 1)
    for i in range(0, len(x)):
        if x[i] is None:
            continue
        x[i] = (math.exp(x[i]) - 1) / (sum + 0.00001)
    return x


def difference(governer, examinee):
    misses = 0
    diff_sum = 0
    total = 0

"""
OLD RECOMMENDER CODE
"""


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
