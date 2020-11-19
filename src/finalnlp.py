# %tensorflow_version 1.x

# !pip install benepar
# !python -m spacy download en
# !pip install -U spacy==2.2.4

# nltk.download("stopwords")
# nltk.download("punkt")
# nltk.download('wordnet')
# benepar.download('benepar_en2')

import benepar
from benepar.spacy_plugin import BeneparComponent
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy

nlp = spacy.load('en_core_web_sm')
nlp.add_pipe(BeneparComponent('benepar_en2'))


stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def split_sentence(info , text , letter ,sentences, sen, flags, op):
  doc = nlp(text)
  sent = list(doc.sents)[0]
  string = sent._.parse_string
  string = string.replace("(", "")
  string = string.replace(")", "")
  string = string.split()
  #print(string)

  info[letter].append({})
  part = ""
  i = 0
  n = len(string)
  temp_onwer = ""

  while(i < n):
      if(string[i] == 'NP' and flags['NP'] == 0):
        # flags['NP'] = 1
        while(i < n and string[i] != 'VP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          i += 1
        info[letter][1]['N'] = part.strip()
        if(i < n):
          flags['NP'] = 1
        part = ""

      elif(string[i] == 'VP' and flags['VP'] == 0):
        flags['VP'] = 1
        while(i < n):
          if(string[i].startswith("VB")):
            info[letter][1]['V'] = string[i + 1]
            i += 2
            break
          else:
            i += 1
        while(i < n and string[i] != 'PP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          if(string[i] == 'NNP'):
            temp_onwer = string[i + 1]
            i += 1
          i += 1
        part += temp_onwer
        if(part):
          info[letter][1]['AV'] = part.strip()
        part = ""

      elif(string[i] == 'PP'):
        while(i < n):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          i += 1
        if(part):
          info[letter][1]['P'] = part.strip()
        flags['NP'] = flags['VP'] = flags['PP'] = 0
        part = ""
        #if(text[-1] != '.'):
         # text += '.'
          #info[letter][0] = text

      elif(flags['VP']):
        while(i < n and string[i] != 'PP'):
          if(string[i] in sentences[sen] and (string[i] != '.' and string[i] != '?')):
            part += string[i] + ' '
          if(string[i] == 'NNP'):
            temp_onwer = string[i + 1]
            i += 1
          i += 1
        part += temp_onwer
        if(part):
          info[letter][1]['AV'] = part.strip()
        part = ""

      else:
        i += 1

  return text

def parameterize(question):
  func_info = dict()
  for letter in question.keys():
    temp_args = []
    for part in ['N','AV','P']:
      if(part in question[letter][1]):
        for w in question[letter][1][part].split():
          if w not in stop_words:
            temp_args.append(lemmatizer.lemmatize(str.lower(w)))
    # print(temp_args)
    func_info[letter] = lemmatizer.lemmatize(question[letter][1]['V'] , 'v') + "(" + ",".join(temp_args) + ")"
  question.clear()
  question.update(func_info)

def process_question(question , text , sen, sentences, flags, letters, op , ques_expression_list , list_question , nlp_question , nlp_list_question):
  ques = ""
  expression = ""
  words = text.split()
  check = 1

  first_word = str.lower(words.pop(0))
  if(lemmatizer.lemmatize(str.lower(words[0]),'v') == "do"):
    words.pop(0)
  if( first_word == "where" or first_word == "what"):
    check = 0
    words[-1] = words[-1].replace("?" , " x?")
  elif( first_word == "who" ):
    check = 0
    words.insert(0,"x")

  text = " ".join(words)

  if(check):
    nlp_question.append(text)
  else:
    nlp_list_question.append(text)

  for term in word_tokenize(text):
    if(term not in op and term != "?"):
      ques += term + ' '
    else:
      #print("ques:",ques)
      ques = ques.strip()
      letter = letters.pop(0)
      question[letter] = list()
      question[letter].append(ques)

      if("not" in ques):
        expression += '~ '
        #print("~" , end=" ")
        l = ques.split()
        ind = l.index("not")
        l.pop(ind)
        ques = " ".join(l)

      if(term == '?'):
        ques += term
        expression += letter + ' '
        #print(letter, end = " ")
        if(check):
          ques_expression_list.append(expression.strip())
        else:
          list_question.append(expression.strip())
        expression = ""
        #print()
      else:
        expression += letter + ' ' + op[term] + ' '
        #print(letter, op[term], end = " ")

      question[letter][0] = ques
      sentences[sen] = ques
      split_sentence(question , ques , letter ,sentences, sen, flags, op)

      ques = ""

def process_query(q, op, letters, info = dict(), question = dict(), expression_list = list() , ques_expression_list = list() , nlp_question = list() , list_question = list() , nlp_list_question = list()):
  flags = {'NP' : 0 , 'VP' : 0 , 'PP' : 0}
  sentences = []
  sen = 0
  expression = ""

  tokenized = sent_tokenize(q)
  # print(tokenized)

  for statement in tokenized:
    #print(statement)
    sentences.append(statement)
    if("?" in statement):
      # print("inside if ?", question)

      process_question(question, statement, sen, sentences, flags, letters, op , ques_expression_list , list_question ,  nlp_question , nlp_list_question)
      # print("in process_query", question)
    else:
      text = ""
      for term in word_tokenize(statement):
        if (term not in op):
          if (term != "if"):
            text += term + ' '
        else:
          # print("op", term)
          text = text.strip()
          letter = letters.pop(0)
          if("not" in text):
            expression += '~ '
            #print("~" , end=" ")
            l = text.split()
            ind = l.index("not")
            l.pop(ind)
            l.pop(ind-1)
            text = " ".join(l)

          if(term == '.'):
            text += term
            expression += letter + ' '
            #print(letter, end = " ")
            expression_list.append(expression.strip())
            expression = ""
            #print()
          else:
            expression += letter + ' ' + op[term] + ' '
            #print(letter, op[term], end = " ")

          info[letter] = list()
          info[letter].append(text)
          string = split_sentence(info, text, letter, sentences, sen, flags, op)
          text = ""
    flags['NP'] = flags['VP'] = flags['PP'] = 0
    sen += 1
  #print("info" , info)
  # resolve conjunctions and merge parts of sentences
  resolve_conjunction(info , '.')
  resolve_conjunction(question , '?')

def resolve_conjunction(info , delim):
  no_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
  yes_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }

  letter_count = 0
  for letter in info.keys():
    letter_count += 1
    for part in no_parts.keys():
      if(part not in info[letter][1]):
        no_parts[part].append(letter)
      else:
        yes_parts[part].append(letter)
    if(info[letter][0][-1] == delim):
      # print(letter_count,no_parts, yes_parts)
      for part in no_parts.keys():
        if (len(no_parts[part]) < letter_count and len(yes_parts[part]) < letter_count):
            #print(part)
            for ele in no_parts[part]:
              ele_to_merge = yes_parts[part][0]
              info[ele][1][part] = info[ele_to_merge][1][part]
      no_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
      yes_parts = {'N' : [] , 'V' : [] , 'AV' : [] , 'P' : [] }
      letter_count = 0

  for letter in info.keys():
    temp_text = ""
    for part in no_parts.keys():
      if(part in info[letter][1]):
        temp_text += info[letter][1][part] + ' '
    info[letter][0] = temp_text.strip()
  # print("info inside process_query", info)

def map_var(questions, facts , expression):
  #print(questions)
  new_questions = dict()
  rev_facts = {v: k for k, v in facts.items()}
  for var in questions:
    param = questions[var]
    if param in rev_facts:
      new_questions[rev_facts[param]] = param
      for i in range(len(expression)):
        #print("hi" , var, expr , rev_facts[param])
        if var in expression[i]:
          expression[i] = expression[i].replace(var , rev_facts[param])
    else:
      new_questions[var] = param
  questions.clear()
  questions.update(new_questions)

# f = {'a': 'go(mary,school)', 'b': 'go(john,school)'}
# q = {'c': 'go(mary,school)', 'd': 'go(ram,school)', 'e': 'go(john,school)'}
# map_var(q,f)
# print(q,f)

def split_facts(allFacts):
  conditionals = list()
  facts = list()
  for expr in allFacts:
    if ( '-' in expr):
      conditionals.append(expr)
    else:
      facts.append(expr)
  return [conditionals , facts]

def user_input(query):
  op = {'and' : '^', 'or' : 'v', '.' : '.' , 'then' : '-' }
  letters = [chr(x) for x in range(ord('a'), ord('z') + 1)]
  info = dict()
  question = dict()
  nlp_question = [] #questions in text
  nlp_list_question = []
  list_question = [] #list kind of questions
  expression_list = list()
  ques_expression_list = list()
  process_query(query, op, letters, info, question , expression_list , ques_expression_list , nlp_question , list_question , nlp_list_question)
  parameterize(question)
  parameterize(info)
  map_var(info, info , expression_list)
  map_var(question, info , ques_expression_list)
  return [expression_list, ques_expression_list , info, question , nlp_question , list_question , nlp_list_question]

def NLP_main(query):
  allFacts, questions, predFacts, predQuest , nlp_question , list_question , nlp_list_question = user_input(query)
  conditionals , facts = split_facts(allFacts)
  print("Boolean Expressions:")
  print("Facts: " , allFacts)
  print("Questions : " , questions)
  print("List Questions : " , list_question)
  print("Predicate Representation :")
  print("Facts: " , predFacts)
  print("Question: ", predQuest)
  return (conditionals, facts, questions, predFacts, predQuest , nlp_question , list_question , nlp_list_question)

# query = "Mary ate bread and jam. What did mary eat?"
# NLP_main(query)

#a = NLP_main("Mary went to school and John did not. If Mary and john went to school then ram did not. Did mary and ram go to school? Did john not go to school?")
# query = "Mary went to school and John did not. If Mary and john went to school then ram did not. Did mary and ram go to school? Did john not go to school?"
# NLP_main(query)
# # query = "John and Ram or Sita went home. Mary did not go to school."
# # query = "Sam had 34 nickels and 43 gems in his bank. Does he have 43 gems in his bank?"
# # query = "Ram went to school and John did not go to school."
# # query = "Birds fly. Crow flies. Are crows birds?"


# q = "Mary went to school and John did not. Did mary go to school?"
# # q = "John and Ram or Sita went to home. Mary did not go to school."
# # q = "Sam had 34 nickels and 43 gems in his bank."
# # q = "Ram went to school and John did not go to school."
# # q = "Birds fly. Crow flies. Is crow a bird?"
