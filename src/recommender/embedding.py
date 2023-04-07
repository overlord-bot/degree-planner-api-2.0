from absl import logging

import tensorflow as tf

import tensorflow_hub as hub
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import re
import seaborn as sns

class Sentence_Embedder():

    def __init__(self):

        self.module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
        self.model = hub.load(self.module_url)
        print ("module %s loaded" % self.module_url)

    def embed(self, input):
        return self.model(input)

    """word = "Elephant"
    sentence = "I am a sentence for which I would like to get its embedding."
    paragraph = (
        "Universal Sentence Encoder embeddings also support short paragraphs. "
        "There is no hard limit on how long the paragraph is. Roughly, the longer "
        "the more 'diluted' the embedding will be.")
    messages = [word, sentence, paragraph]"""


    '''
    Parameters:
        message_embeddings (numpy list): the return value of the embed function
    Returns:
        list: a python list of embeddings
    '''
    def read_embeddings(self, message_embeddings) -> list:
        vector = []
        for i, message_embedding in enumerate(np.array(message_embeddings).tolist()):
            vector.append(message_embedding)
            # print(f"Embedding size: {len(message_embedding)}")
            # message_embedding_snippet = ", ".join((str(x) for x in message_embedding[:3]))
            # print(f"Embedding: [{message_embedding_snippet}, ...]\n")        
        return vector
