import os
import numpy as np
import tensorflow as tf
from preprocess import *
from transformer_model import Transformer_Seq2Seq
import sys
import random
import pickle

# True: allows user to input passwords and check strength
# False: runs the test set
USER_INPUT = False

def train(model, train_french, train_english, eng_padding_index):
	"""
	Runs through one epoch - all training examples.

	:param model: the initialized model to use for forward and backward pass
	:param train_french: french train data (all data for training) of shape (num_sentences, 14)
	:param train_english: english train data (all data for training) of shape (num_sentences, 15)
	:param eng_padding_index: the padding index, the id of *PAD* token. This integer is used when masking padding labels.
	:return: None
	"""

	# NOTE: For each training step, you should pass in the french sentences to be used by the encoder, 
	# and english sentences to be used by the decoder
	# - The english sentences passed to the decoder have the last token in the window removed:
	#	 [STOP CS147 is the best class. STOP *PAD*] --> [STOP CS147 is the best class. STOP] 
	# 
	# - When computing loss, the decoder labels should have the first word removed:
	#	 [STOP CS147 is the best class. STOP] --> [CS147 is the best class. STOP] 
    
	inds = np.arange(len(train_french))
	inds = tf.random.shuffle(inds)
	train_french = tf.gather(train_french, inds)
	train_english = tf.gather(train_english, inds)

	stopper = 0

	for i in range(0, len(train_french), model.batch_size):
		stopper += 1
		image = train_french[i:i + model.batch_size]
		label = train_english[i:i + model.batch_size]
		label = np.delete(label, -1, 1)
		label2 = np.delete(train_english[i:i + model.batch_size], 0, 1)
		mask = label2 != eng_padding_index

		with tf.GradientTape() as tape:
			preds = model([image, label])
			loss = model.loss_function(preds, label2, mask)
		if stopper % 10 == 0:
			acc = model.accuracy_function(preds, label2, mask)
			print("LOSS: {} | ACCURACY: {}".format(loss.numpy(), acc))

		gradients = tape.gradient(loss, model.trainable_variables)
		model.opt.apply_gradients(zip(gradients, model.trainable_variables))

def test(model, test_french, test_english, eng_padding_index):
	"""
	Runs through one epoch - all testing examples.

	:param model: the initialized model to use for forward and backward pass
	:param test_french: french test data (all data for testing) of shape (num_sentences, 14)
	:param test_english: english test data (all data for testing) of shape (num_sentences, 15)
	:param eng_padding_index: the padding index, the id of *PAD* token. This integer is used when masking padding labels.
	:returns: a tuple containing at index 0 the perplexity of the test set and at index 1 the per symbol accuracy on test set, 
	e.g. (my_perplexity, my_accuracy)
	"""

	# Note: Follow the same procedure as in train() to construct batches of data!
    
	loss_tracker = 0.0
	acc_tracker = 0.0
	total_words = 0

	for i in range(0, len(test_french), model.batch_size):
		image = test_french[i:i + model.batch_size]
		label = test_english[i:i + model.batch_size]
		label = np.delete(label, -1, 1)
		preds = model([image, label])

		label2 = np.delete(test_english[i:i + model.batch_size], 0, 1)
		mask = label2 != eng_padding_index
		batch_word_count = tf.cast(tf.reduce_sum(mask * 1), tf.float32)
		total_words += batch_word_count
		loss = model.loss_function(preds, label2, mask)
		acc = model.accuracy_function(preds, label2, mask)
		loss_tracker += loss
		acc_tracker += (acc * batch_word_count)

	return np.exp(loss_tracker / total_words), (acc_tracker / total_words)
	

def main():

	# Change this to False to run the test set rather than a prediction
	global USER_INPUT
	passw = ""

	if len(sys.argv) != 2:
			print("USAGE: python model.py <password>")
			exit()
	else:
		passw = sys.argv[1]

	english_vocab = {}
	french_vocab = {}

	with open('eng.pkl', 'rb') as handle:
		english_vocab = pickle.load(handle)

	with open('fre.pkl', 'rb') as handle:
		french_vocab = pickle.load(handle)

	model = tf.keras.models.load_model('./myModel', compile=False)

	text = []
	labels = []
	text.append([char for char in passw])
	labels.append([])
	text, labels = pad_corpus(text, labels)
	text = convert_to_id(french_vocab, text)
	labels = convert_to_id(english_vocab, labels)
	preds = model.call([text, labels])
	preds = tf.argmax(input=preds, axis=2)[0]
	if preds[0] == 4:
		print("WEAK")
	elif preds[0] == 5:
		print("MEDIUM")
	elif preds[0] == 6:
		print("STRONG")
	else:
		print("WEAK")

if __name__ == '__main__':
	main()
