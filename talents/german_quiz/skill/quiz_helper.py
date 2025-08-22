from dataclasses import dataclass
import re
from ..content import Question




@dataclass
class Recognition:
    stop: bool = False
    bad_question: bool = False
    skip_question: bool = False
    correct_answer: bool = False
    incorrect_article: bool = False
    incorrect_plural: bool = False
    incomplete_grammar: bool = False

    @property
    def correct_grammar(self) -> bool:
        return not self.incomplete_grammar and not self.incorrect_plural and not self.incorrect_article


article_to_genus = {'die': 'f', 'das': 'n', 'der':'m'}
genus_to_article = {v:k for k,v in article_to_genus.items()}

class QuizHelper:
    def __init__(self, word_symbols: set[str], stop_intent, bad_question_intent, pass_intent):
        self.word_symbols = word_symbols
        self.stop_intent = self.standardize_to_str(stop_intent)
        self.pass_intent = self.standardize_to_str(pass_intent)
        self.bad_question_intent = self.standardize_to_str(bad_question_intent)

    def standardize_to_tuple(self, text) -> tuple[str,...]:
        s = ''.join(self.word_symbols)
        words = re.split(f'[^{s}]',text)
        return tuple(w.lower() for w in words if w!='')

    def standardize_to_str(self, text) -> str:
        return ' '.join(self.standardize_to_tuple(text))

    def standardize_one_word(self, text) -> 0:
        value = self.standardize_to_tuple(text)
        if len(value)!=1:
            raise ValueError(f"Expected exactly one word, but was {value}")
        return value[0]

    def validate_answer(self, question: Question, s: str) -> Recognition:
        std_text = self.standardize_to_str(s)
        print(std_text)

        if std_text == self.stop_intent:
            return Recognition(stop=True)
        if std_text == self.bad_question_intent:
            return Recognition(bad_question=True)
        if std_text == self.pass_intent:
            return Recognition(skip_question=True)

        words = self.standardize_to_tuple(s)
        std_answer = self.standardize_one_word(question.answer)
        try:
            answer_index = words.index(std_answer)
        except:
            return Recognition()

        incomplete = Recognition(correct_answer=True, incomplete_grammar=True)
        if answer_index == 0:
            return incomplete
        if len(words) < answer_index+2:
            return incomplete
        if words[answer_index+1] != 'die':
            return incomplete

        result = Recognition(correct_answer=True)

        genus = article_to_genus[words[answer_index-1]]
        if genus not in question.genus:
            result.incorrect_article = True

        plurals = [self.standardize_one_word(w) for w in question.plural]
        if words[answer_index+2] not in plurals:
            result.incorrect_plural = True
        return result


    def whisper_prompt(self, question: Question):
        result = ["Ich soll jetzt sagen: "]
        result.append(f'"{self.stop_intent}", ')
        result.append(f'"{self.bad_question_intent}"')
        result.append(f'"{self.pass_intent}"')
        result.append(". ")
        result.append("Oder soll ich die Antwort geben. ")
        result.append("Die Antwort ist: ")

        answers = []
        answers.append(question.answer)
        if 'f' in question.genus:
            answers.append("eine "+question.answer)
        if "m" in question.genus or 'n' in question.genus:
            answers.append("ein "+question.answer)

        if len(question.genus) == 1 and len(question.plural) == 1:
            answers.append(genus_to_article[question.genus[0]]+' '+question.answer+', die '+question.plural[0])
        else:
            for g in question.genus:
                answers.append(genus_to_article[g]+' '+question.answer)
            for p in question.plural:
                answers.append("die "+p)
        result.append(", ".join('"'+a+'"' for a in answers))
        result.append('. Ich kann auch ein Fehler machen und etwas anderes sagen. So jetzt sage ich: ')
        return ''.join(result)

    def right_answer(self, question: Question):
        if len(question.genus) == 1 and len(question.plural) == 1:
            result = genus_to_article[question.genus[0]]+' '+question.answer+', die '+question.plural[0]
        else:
            singular = ', '.join(genus_to_article[g] + ' ' + question.answer for g in question.genus)
            plural = ', '.join('die '+p for p in question.plural)
            result = singular+'. Plural: '+plural
        result = result[0].upper() + result[1:]
        return result

    def question_to_ask(self, question: Question):
        return f'{question.topic}. {question.question}'






