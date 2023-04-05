import numpy as np

from ..math.sorting import *
from ..recommender.embedding import Sentence_Embedder
from ..io.output import *

class Recommender():

    def __init__(self, catalog):

        self.catalog = catalog
        self.embedder = Sentence_Embedder()
        
        self.tag_embeddings_cache = dict()
        self.debug = Output(OUT.DEBUG)
    
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

                # accessing stored embedding caches
                tag_embedding = self.tag_embeddings_cache.get(tag, None)
                if tag_embedding is None:
                    tag_embedding = self.embed_message([tag])[0]
                    self.tag_embeddings_cache.update({tag:tag_embedding})

                course_embedding = course.embedding
                if course_embedding is None:
                    course_embedding = self.embed_message([course.attr('name')])[0]
                    course.embedding = course_embedding
                course_relevance_scores[i] = self.array_similarity(course_embedding, tag_embedding)
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
        self.debug.print(f'overall relevances for each subject: {overall_relevances}')

        # compute relevance of each individual course and compare to overall_relevances based on course subject
        for course in recommending_courses:
            subject = course.attr('subject')
            course_relevance_scores = self.get_course_relevances(course)
            if course_relevance_scores is None:
                relevance.update({course : -1})
                continue
            similarity = self.array_similarity(overall_relevances.get(subject), course_relevance_scores)
            relevance.update({course : similarity})

        sorted_relevances = dictionary_sort(relevance, True)

        self.debug.print('relevances by embedding: ' + str(['course: ' + str(c) + ' score: ' + str(s) + '\n' for c,s in sorted_relevances]))
        return relevance


    def embed_message(self, message):
        if not isinstance(message, list):
            message = [message]
        embedded_messages = self.embedder.embed(message)
        return embedded_messages
