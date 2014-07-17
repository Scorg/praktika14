import sys
import re

def isTerminal(c):
	if ".!?".find(c) >= 0:
		return True
	return False

def isBracketOpen(c):
	if "(".find(c) >= 0:
		return True
	return False

def isBracketClose(c):
	if ")".find(c) >= 0:
		return True
	return False

def isSpeechSign(c):
	if c=="\"":
		return True
	return False

def doNonRE(lines: list) -> list:
	nBracketsOpened=0
	bSpeech=False
	#isWord=0 # 0 = пробел, 1 = слово, 2 = знаки препинания
	#bTerminating=False
	terminatingStage=0 # 0 - нет, 1 - знак препинания, 2 - пробел
	buf = ""
	sentences = []

	for line in lines:
		print(line)

		for i in range(len(line)):
			c = line[i]

			if isSpeechSign(c):
				bSpeech = not bSpeech

				if bSpeech:
					if terminatingStage==1:
						terminatingStage = 0 #Если входим в кавычки, сбрасываем состояние

			if not bSpeech:
				if isBracketOpen(c):
					if nBracketsOpened==0:
						if terminatingStage==2:
							sentences.append(buf[:-1])
							buf = ""
						
						terminatingStage = 0

					nBracketsOpened += 1

				if isBracketClose(c):
					if nBracketsOpened>0:
						nBracketsOpened -= 1

			if nBracketsOpened==0:
				if isTerminal(c):
					if terminatingStage==0:
						terminatingStage = 1

				elif not bSpeech:
					if c==' ':
						if terminatingStage==1:
							terminatingStage = 2

					elif c=='\n':
						terminaingStage = 2
					
					elif (c.isalpha() and c.isupper()) or c.isnumeric():
						if terminatingStage==2:
							sentences.append(buf[:-1])
							buf = ""
						
						terminatingStage = 0

				elif bSpeech:
					if isSpeechSign(c): #Началась прямая речь
						if terminatingStage==2:
							sentences.append(buf[:-1])
							buf = ""

						terminatingStage = 0

			buf += c
					
				#if isWord==0 and c.isalnum(c):
				#	isWord=1
				#	continue

				#if isWord==1

	sentences.append(buf)
	buf = ""
	return sentences

def doRE(lines: list) -> list:
	nBracketsOpened=0
	bSpeech=False
	terminatingStage=0 # 0 - нет, 1 - знак препинания, 2 - пробел

	sentences = []
	buf = ""

	#Выражение вне скобок и кавычек
	expDefault = re.compile(r"[^(\".!?\n]*?([(\"\n]|[.!?]+)")
	#Выражение внутри кавычек
	expSpeech = re.compile(r"[^\"]*?\"")
	#Выражение внутри скобок
	expBrackets = re.compile(r"[^()\"]*?[()\"]")
	#Выражение для проверки ФИО назад
	expNameBack = re.compile(r"([ЁА-Я][а-я\-]+ )?([ЁА-Я]\. ?)?([ЁА-Я]\.)$")
	#Выражения для проверки ФИО вперёд
	expNameForw1 = re.compile(" ?[ЁА-Я]\.[^\w]")
	expNameForw2 = re.compile(" ?([ЁА-Я]\.)? ?[ЁА-Я][ёа-я]+")

	i = 0
	while i<len(lines):
		line = lines[i]
		#print(line)
		
		pos = 0
		length = len(line)

		while pos < length:
			match = None

			if bSpeech:
				match = expSpeech.match(line[pos:])
			elif nBracketsOpened>0:
				match = expBrackets.match(line[pos:])
			else:
				match = expDefault.match(line[pos:])

			if match:
				c = match.group()[-1]
				buf += match.group()

				if isSpeechSign(c):
					bSpeech = not bSpeech

					if not bSpeech:
						term = re.match(r"[.!?]\"( [+\-\"(ЁА-Я0-9])|\n", line[pos+match.end()-2:])

						if term:
							#buf += match.group()
							sentences.append(buf)
							buf = ""
							pos += 1 #не помешает ли другим веткам?
					
				elif isBracketOpen(c):
					nBracketsOpened += 1

				elif isBracketClose(c) and nBracketsOpened>0:
					nBracketsOpened -= 1

				elif nBracketsOpened==0:
					term = re.match(r"[.!?]( [+\-\"(ЁА-Я0-9]|\n)", line[pos+match.end()-1:])
					bTerminate = True

					#backMatch = expNameBack.search(match.group())
					backMatch = expNameBack.search(buf)

					if backMatch:
						forwMatch = None

						if backMatch.group(1): #Если не одна заглавная буква
							if not backMatch.group(2): #Если не полное ФИО
								forwMatch = expNameForw1.match(line[pos+match.end():])
						else:
							forwMatch = expNameForw2.match(line[pos+match.end():])

						if forwMatch:
							bTerminate = False

					if term and bTerminate:
						sentences.append(buf)
						buf = ""
						pos += 1 #не помешает ли другим веткам?
					elif c=='\n' and i<len(lines)-1 and re.match(r"[+\-\"(ЁА-Я0-9]", lines[i+1]):
						sentences.append(buf[:-1])
						buf = ""

				pos += match.end()
			else:
				buf += line[pos:]
				pos = length 

		i += 1

	if len(buf)>0:
		sentences.append(buf)
	buf = ""

	#print("Остаток: '" + buf + "'")
	return sentences


lines = [] #список будущих строчек получаемого текста
sentences = []

#читаем строчки из указанного стандартного потока
#если после имени скрыпта указано '< [имя_файла]',
#чтение будет производиться из него
for line in sys.stdin:
	#if line.endswith('\n'):
	#	line = line[0:-1] #Обрезаем знак переноса, если присутствует (всегда будет, похоже)
	lines.append(line)


#sentences = doNonRE(lines)
sentences = doRE(lines)

print("Предложения (%d):" % len(sentences))

i=1
for s in sentences:
	print(("#%d: " % i) + s)
	i+=1