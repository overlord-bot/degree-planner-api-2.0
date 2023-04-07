import nltk
from collections import Counter

# Step 1: Tokenize the paragraph
tokens = nltk.word_tokenize(paragraph)

# Step 2: Remove stop words
tokens = [token.lower() for token in tokens if token.isalpha() and token.lower() not in nltk.corpus.stopwords.words('english')]

# Step 3: Calculate word frequencies
word_freq = Counter(tokens)

# Step 4: Sort the words by frequency
sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

# Step 5: Select the top keywords
keywords = [word[0] for word in sorted_words[:10]]

# Step 6: Optional - Apply part-of-speech tagging
pos_tags = nltk.pos_tag(tokens)
nouns = [word[0] for word in pos_tags if word[1] in ['NN', 'NNS', 'NNP', 'NNPS']]
noun_freq = Counter(nouns)
sorted_nouns = sorted(noun_freq.items(), key=lambda x: x[1], reverse=True)
noun_keywords = [word[0] for word in sorted_nouns[:10]]
