import numpy as np
from .sorting import dictionary_sort


def array_similarity(vec1, vec2):
    return np.linalg.norm(np.add(vec1, np.multiply(vec2, -1))).item()

def soft_max(x):
    sum = 0
    for i in range(0, len(x)):
        sum += np.exp(x[i])
    for i in range(0, len(x)):
        x[i] = (np.exp(x[i])) / sum
    return x
    
def hard_max(x, adjust=0.95):
    sum = 0
    for i in range(0, len(x)):
        sum += np.exp(x[i]) - adjust
    for i in range(0, len(x)):
        x[i] = (np.exp(x[i]) - adjust ) / sum
    return x

def scale_array(array, additive, multiplicative):
    return np.add(np.dot(array, multiplicative), additive)

def scale_dictionary_values(dictionary, additive, multiplicative, key=None):
    if key is not None:
        dictionary.update({key : scale_array(dictionary.get(key), additive, multiplicative)})
        return
    for key in dictionary.keys():
        dictionary.update({key : scale_array(dictionary.get(key), additive, multiplicative)})
    
def best_descriptors(descriptors, amount:int, threshold:float):
    sorted_descriptors = dictionary_sort(descriptors, True)[:amount]
    best_descriptors = list()
    for tag, tag_relevance in sorted_descriptors:
        if tag_relevance < threshold:
            best_descriptors.append(f'{tag} ({int(1 / tag_relevance)}%)')
    return best_descriptors
