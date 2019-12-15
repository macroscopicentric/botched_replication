import nltk
import redis

import random
import collections
import time
import json
import re
import sys
import os

# Based on my best estimate of a pandoravirus's mutation rate. Mutation rates
# vary widely between taxa. I arbitrarily picked pandoraviruses because a) I
# wanted something fast enough to watch, and viruses have some of the fastest
# mutation rates; b) the name is awesome; and c) memes are viral too, which is
# the idea I wanted to explore.

# Base pairs: 2,200,000 (https://en.wikipedia.org/wiki/Pandoravirus)
# Replication cycle: 12.5 hours (avg) (http://science.sciencemag.org/content/341/6143/281.full)
# Rate of replication: .22 per generation (generic, based on https://en.wikipedia.org/wiki/Mutation_rate)
# Timespan between mutations: 56.8 hours
# Timespan sped up by x1000: 3.4 min (because we all have lives to live)
MUTATION_RATE_IN_SECONDS = 204

class Corpus(object):

	def __init__(self, redis_connection, filename):
		self.corpus_shortname = re.sub(r'\..+', '', filename)
		self.redis_original_text_key = self.corpus_shortname + ':original_text'
		self.redis_modified_text_key = self.corpus_shortname + ':modified_text'
		self.redis_changes_key = self.corpus_shortname + ':changes'

		with open(filename) as f:
			raw_text = f.read()

		# Just set corpus original_text key every time.
		self.redis = redis_connection
		self.redis.set(self.redis_original_text_key, raw_text)

		modified_text = self.redis.get(self.redis_modified_text_key).decode('utf-8')

		if modified_text:
			self.tokens = self.tokenize(modified_text)
		else:
			self.tokens = self.tokenize(raw_text)
			self.save_mutated_text()


	def tokenize(self, text):
		'''
		Tokenize the given text. Using word_tokenize() on a list of sentences
		from sent_tokenize() instead of the raw text because this is supposed
		to be more efficient, but requires flattening the resulting list of lists.
		'''
		return sum(map(nltk.word_tokenize, nltk.sent_tokenize(text)), [])


	def untokenize(self):
		'''
		Reverse the effects of NLTK Penn Treebank tokenization.
		'''
		rejoined_text = ' '.join(self.tokens)
		punctuation = ["'", '"', '!', '.', ',', ';', ':', '?']
		for mark in punctuation:
			rejoined_text = rejoined_text.replace(" {0}".format(mark), mark).replace("`` ", ' "').replace("''", '"')
		rejoined_text = rejoined_text.replace("( ", "(").replace(" )", ")")
		rejoined_text = rejoined_text.replace("< p > ", "<p>").replace(" < /p >", "</p>")
		return rejoined_text


	def words_with_pos(self):
		'''
		Build a list of tuples where the first element of each tuple is a token
		and the second element is its part of speech. This is a method and not
		an attribute because it should change every time self.tokens changes. 
		'''
		return nltk.pos_tag(self.tokens)


	def pos_dictionary(self, words_with_pos):
		'''
		Build a dictionary where the keys are the parts of speech and the
		values are lists of all words from the corpus that are that POS. This
		is a method and not an attribute because it should change every time
		self.tokens changes.
		'''
		pos_dictionary = collections.defaultdict(list)
		for word_and_pos in self.words_with_pos():
			word, pos = word_and_pos
			# Edge case: 'p' ends up in the tokens list multiple times because
			# of the <p> tags. Don't include those in the pos_dictionary.
			if word.isalpha() and word != 'p':
				pos_dictionary[pos].append(word)
		return pos_dictionary


	def word_to_mutate(self, words_with_pos):
		'''
		Pick a word from the corpus to mutate and remember its index.
		'''
		index = random.randrange(0, len(words_with_pos))
		word, pos = words_with_pos[index]

		# Don't bother mutating punctuation. That's boring. Also don't mutate
		# 'p', because that's the middle of a paragraph tag from the HTML.
		if not word.isalpha() or word == 'p':
			word, pos, index = self.word_to_mutate(words_with_pos)

		return word, pos, index


	def mutate_word(self):
		'''
		Pick a word from the corpus and replace it with another word from the
		corpus that's the same part of speech.
		'''
		words_with_pos = self.words_with_pos()
		original_word, pos, index = self.word_to_mutate(words_with_pos)

		replacement = random.choice(self.pos_dictionary(words_with_pos)[pos])
		formatted_replacement = self.format_replacement_word(replacement, original_word)

		self.tokens[index] = formatted_replacement
		return {'original_word': original_word, 'replacement_word': formatted_replacement, 'index': index}


	def format_replacement_word(self, replacement_word, original_word):
		'''
		Helper method to normalize some side effects of minimal token
		formatting, including ensuring the replacement word is cased the same
		way as the original word.
		'''
		if original_word.islower():
			formatted_replacement = replacement_word.lower()
		else:
			formatted_replacement = replacement_word.capitalize()

		# Edge case: default Penn Treebank tokenizer doesn't always make periods
		# at the end of sentences into separate tokens.
		if '.' in original_word and not '.' in formatted_replacement:
			formatted_replacement += '.'

		if '.' not in original_word and '.' in formatted_replacement:
			formatted_replacement = formatted_replacement.replace('.', '')

		return formatted_replacement


	def save_mutated_text(self):
		'''
		Save the current version of the text with all changes to Redis.
		'''
		modified_text = self.untokenize()
		self.redis.set(self.redis_modified_text_key, modified_text)


	def fetch_current_text(self):
		'''
		Fetch current version of modified text from Redis.
		'''
		return self.redis.get(self.redis_modified_text_key).decode('utf-8')


	def save_newest_change(self, newest_change):
		'''
		Save the newest change as the latest item in the sorted set of changes
		in Redis.
		'''
		self.redis.zadd(self.redis_changes_key, json.dumps(newest_change), time.time())


	def fetch_newest_change(self):
		'''
		Fetch most recent change and its timestamp from Redis.
		'''
		change_and_timestamp = self.redis.zrange(self.redis_changes_key, -1, -1, withscores=True)[0]
		return self.format_redis_change(change_and_timestamp)


	def fetch_all_changes_since(self, timestamp):
		'''
		Fetch an array of changes since the timestamp.
		'''
		changes = self.redis.zrangebyscore(self.redis_changes_key, timestamp, time.time(), withscores=True)
		return map(self.format_redis_change, changes)


	def format_redis_change(self, change_and_timestamp):
		'''
		Given a tuple from Redis of a change and its timestamp, turn it back
		into a dictionary and then insert the timestamp into the dictionary.
		'''
		change, timestamp = change_and_timestamp
		formatted_change = json.loads(change)
		formatted_change['timestamp'] = timestamp
		return formatted_change


	def mutate(self):
		'''
		Change a word, save the entirety of the new text, and record the change.
		'''
		newest_change = self.mutate_word()

		self.save_mutated_text()
		self.save_newest_change(newest_change)

		summary = "Saved change {0} to Redis.".format(newest_change)
		return summary


if __name__=='__main__':
	r = redis.from_url(os.environ.get('REDIS_URL'))
	# Pass in the text file name.
	text = Corpus(r, sys.argv[1])
	while True:
		print(text.mutate())
		time.sleep(MUTATION_RATE_IN_SECONDS)
