
"""
The creative chatbot
finds words it knows and puts them in template sentences

failing that it uses a backup sentence
"""

import string, random, re

def choose(ls):
    """pops a random item from a list"""
    if len(ls):
        index = random.choice(range(len(ls)))
        return ls.pop(index)
    else: return None
    
                 
class Sentence(object):
    """A sentence is a list of words"""
    def __init__(self,sentence):
    	self.punct = sentence[-1]
    	if self.punct not in '?!.': self.punct = ''
        wordList = re.findall(r'([a-z-]+)',sentence.lower())

        self.words = [Word(w) for w in wordList]
        
    def supportedWords(self):
        """
        returns a list of the words in the sentence that are supported.
        we only support verbs, nouns and adjectives. anything else is not included.
        ex: I have a big dog -> ['I','have','big','dog']
        """
        return [word for word in self.words if word.supported()]
    
    def starred(self,word):
	"""
	replaces the *** with word
	"""
    	s=''
    	for w in self.words:
    		if w==word: s+='***'
    		else: s+=w
    		s+=' '
    	s = s[:-1]+self.punct
    	return s

    def __str__(self):
        """allows the sentence to be printed"""
        return ' '.join(self.words)+self.punct


class Word(str):
    """
    A word is a string that knows what part of speech it is.
    If the database does not contain a word, the user is prompted for info.
    """

    filename = 'pos3.txt'
    wordlist = {}
    poslist = {}
    pronouns = 'you me they it that this we us he him her she myself yourself herself himself'.split(' ')
    
    def __init__(self, word):
    	self.pos = Word.wordlist.get(word,'o')

    def supported(self):
        return self.pos in 'vnas'
        
    def parseDB(cls):
        '''
        Parses our own custom database and 
            adds entries to a global dictionary.
        '''
        f = open(cls.filename, 'r')
        for line in f:
            stripped = line.strip('\n')
            parts = stripped.split(' ')
            cls.wordlist[parts[0]] = parts[1]
            cls.poslist[parts[1]] = cls.poslist.get(parts[1],[]) + [parts[0]]
        f.close()
    parseDB = classmethod(parseDB)

    def randomWord(cls):
	return Word(random.choice(Word.wordlist.keys()))
    randomWord = classmethod(randomWord)

    def randomPosWord(cls,pos):
	return Word(random.choice(Word.poslist[pos]))	
    randomPosWord = classmethod(randomPosWord)

###--- load the database!
Word.parseDB()
###---

def nickname(pattern):
	return ''.join([Word.randomPosWord(c).capitalize() for c in pattern])


class ChatBot(object):
    """A ChatBot has a conversation with the user"""
    def __init__(self,filename='chattemplates.txt'):
        self.filename = filename
        self.responses = {'a':[],'n':[],'v':[],'s':[],'o':[]}
        self.parseResponses()

    def parseResponses(self):
        '''
        Parses our own response database and 
            adds entries to a response lists.
        '''
        f = open(self.filename, 'r')
        for line in f:
            stripped = line.strip('\n')
            parts = stripped.split(':')
            self.responses[parts[0]].append(parts[1])
        f.close()
            
    def fillTemplate(self,word):
        if word is None: return None
        template = random.choice(self.responses[word.pos])
        return re.sub('\*\*\*',word,template)
    
    def talk(self,text):
    	s = Sentence(text) ##parse the sentence
    	w = self.chooseWord(s)
	r = self.fillTemplate(w)
      	if r is None: r =  "im tired of talking with you."
    	return r
    	
    
    def chooseWord(self,s):
    	""" returns the longest supported word"""
    	words = [(len(w),w) for w in s.supportedWords() if w not in Word.pronouns]
    	if not words: return Word.randomWord() ##any word
    	words.sort(reverse = True)
    	return words[0][1]
    
    	
    




if __name__ == '__main__':

    print 'Hello. I am '+nickname('an')
    cb = ChatBot()
    while 1:
    	print cb.talk(raw_input())
    	
    	
