import nltk
import random
import collections

class ParsedCorpus(object):

	def __init__(self, file):
		with open(file) as f:
			self.raw_text = f.read()

		self.tokens = nltk.word_tokenize(self.raw_text)
		self.text = nltk.pos_tag(self.tokens)

		self.pos_dictionary = collections.defaultdict(list)
		for word_and_pos in self.text:
			word, pos = word_and_pos
			if pos.isalpha():
				self.pos_dictionary[pos].append(word)


	def word_to_mutate(self):
		index = random.randrange(0, len(self.text))
		word, pos = self.text[index]

		if not pos.isalpha():
			word, pos, index = self.find_word_to_mutate(self)

		return word, pos, index


	def mutate_word(self):
		word_to_replace, pos, index = self.word_to_mutate()
		replacement = random.choice(self.pos_dictionary[pos])
		self.tokens[index] = replacement

	def untokenize(self):
		rejoined_text = ' '.join(self.tokens)
		punctuation = ["'", '"', '!', '.', ',', ';', ':', '?']
		for mark in punctuation:
			rejoined_text = rejoined_text.replace(" {0}".format(mark), mark).replace("`` ", ' "').replace("''", '"')
		rejoined_text = rejoined_text.replace("( ", "(").replace(" )", ")")
		return rejoined_text

	def mutate(self):
		self.mutate_word()
		modified_text = self.untokenize()
		return modified_text


text = ParsedCorpus('library_of_babel.txt')
print text.mutate()
