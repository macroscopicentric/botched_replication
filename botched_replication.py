import nltk
import random
import collections
import time
import csv
import re
import sys

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

class ParsedCorpus(object):

	def __init__(self, filename):
		self.filename = filename
		with open(filename) as f:
			self.raw_text = f.read()

		# Using word_tokenize() on a list of sentences from sent_tokenize()
		# instead of the raw text because this is supposed to be more efficient,
		# but requires flattening the resulting list of lists.
		self.tokens = sum(map(nltk.word_tokenize, nltk.sent_tokenize(self.raw_text)), [])


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

		# Don't bother mutating punctuation. That's boring.
		if not word.isalpha():
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
		return {'original': original_word, 'replacement': formatted_replacement, 'index': index}


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


	def untokenize(self):
		'''
		Reverse the effects of NLTK tokenization.
		'''
		rejoined_text = ' '.join(self.tokens)
		punctuation = ["'", '"', '!', '.', ',', ';', ':', '?']
		for mark in punctuation:
			rejoined_text = rejoined_text.replace(" {0}".format(mark), mark).replace("`` ", ' "').replace("''", '"')
		rejoined_text = rejoined_text.replace("( ", "(").replace(" )", ")")
		rejoined_text = rejoined_text.replace("< p > ", "<p>").replace(" < /p >", "</p>")
		return rejoined_text


	def save_mutated_text(self):
		'''
		Save the current version of the text with all changes.
		'''
		modified_text_filename = 'modified_' + self.filename
		modified_text = self.untokenize()
		with open(modified_text_filename, 'w') as f:
			f.write(modified_text)


	def save_newest_change(self, newest_change):
		'''
		Save the newest change as a row in a csv file.
		'''
		filename_without_extension = re.sub(r'\..+', '', self.filename)
		changes_filename = filename_without_extension + '_changes.csv'
		with open(changes_filename, 'a') as f:
			csvwriter = csv.writer(f)
			csvwriter.writerow([newest_change['original'], newest_change['replacement'], newest_change['index']])


	def mutate(self):
		'''
		Change a word and save the entirety of the new text. Record the change
		in a separate file.
		'''
		newest_change = self.mutate_word()
		self.save_mutated_text()
		self.save_newest_change(newest_change)
		return newest_change


# Pass in the text file name so I can swap easily in Heroku between the original
# text and the modified text without having to modify this script.
text = ParsedCorpus(sys.argv[1])
while True:
	print text.mutate()
	time.sleep(MUTATION_RATE_IN_SECONDS)
