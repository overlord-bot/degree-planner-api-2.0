from absl import logging
import tensorflow_hub as hub
import numpy as np

class Sentence_Embedder():

    def __init__(self):

        self.module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
        self.model = hub.load(self.module_url)
        print ("module %s loaded" % self.module_url)

    def embed(self, input):
        embed = self.model(input)
        #print(f'before normalization: {embed}')
        #embed = tf.nn.l2_normalize(embed, axis=1)
        #print(f'after normalization: {embed}')
        return embed
