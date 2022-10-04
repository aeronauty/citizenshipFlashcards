import logging
import pandas as pd
import os
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from datetime import date


# Some useful methods and facts
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}

stateDict = {'Alabama': 'Montgomery',
              'Alaska': 'Juneau',
              'Arizona': 'Phoenix',
              'Arkansas': 'Little Rock',
              'California': 'Sacramento',
              'Colorado': 'Denver',
              'Connecticut': 'Hartford',
              'Delaware': 'Dover',
              'Florida': 'Tallahassee',
              'Georgia': 'Atlanta',
              'Hawaii': 'Honolulu',
              'Idaho': 'Boise',
              'Illinois': 'Springfield',
              'Indiana': 'Indianapolis',
              'Iowa': 'Des Moines',
              'Kansas': 'Topeka',
              'Kentucky': 'Frankfort',
              'Louisiana': 'Baton Rouge',
              'Maine': 'Augusta',
              'Maryland': 'Annapolis',
              'Massachusetts': 'Boston',
              'Michigan': 'Lansing',
              'Minnesota': 'Saint Paul',
              'Mississippi': 'Jackson',
              'Missouri': 'Jefferson City',
              'Montana': 'Helena',
              'Nebraska': 'Lincoln',
              'Nevada': 'Carson City',
              'New Hampshire': 'Concord',
              'New Jersey': 'Trenton',
              'New Mexico': 'Santa Fe',
              'New York': 'Albany',
              'North Carolina': 'Raleigh',
              'North Dakota': 'Bismarck',
              'Ohio': 'Columbus',
              'Oklahoma': 'Oklahoma City',
              'Oregon': 'Salem',
              'Pennsylvania': 'Harrisburg',
              'Rhode Island': 'Providence',
              'South Carolina': 'Columbia',
              'South Dakota': 'Pierre',
              'Tennessee': 'Nashville',
              'Texas': 'Austin',
              'Utah': 'Salt Lake City',
              'Vermont': 'Montpelier',
              'Virginia': 'Richmond',
              'Washington': 'Olympia',
              'West Virginia': 'Charleston',
              'Wisconsin': 'Madison',
              'Wyoming': 'Cheyenne'}

# invert the dictionary
abbrev_to_us_state = dict(map(reversed, us_state_to_abbrev.items()))

class flashCards(object):
    """
    Creates a flashcard object that enables you to change the content for a given state
    """
    def __init__(self, state="NV", logLevel="WARN"):
        # Make the logger
        self._l = self._get_logger(logLevel)
        self._l.setLevel(logging.DEBUG)

        # Find out the state and store in the object
        self._state = state
        self._l.debug(f"State set as {state} - {abbrev_to_us_state[state]}")

        # Get the list of senators and represenatives
        electedFolks = ['https://ballotpedia.org/List_of_current_members_of_the_U.S._Congress']

        # Get the senators
        senatorData = pd.read_html(electedFolks[0])[3]

        # Filter tha data
        self._senators = senatorData[senatorData.stack().str.contains(abbrev_to_us_state[state]).groupby(level=0).any()]["Name"].to_list()
        self._l.debug(f"The state senators for {abbrev_to_us_state[state]} are {', '.join(self._senators)}")

        # Get the representatives
        representativeData = pd.read_html(electedFolks[0])[6]  # gets all the tables from the url
        self._representatives = \
        representativeData[representativeData.stack().str.contains(abbrev_to_us_state[state]).groupby(level=0).any()][
            "Name"].to_list()
        self._l.debug(f"The state House Representatives for {abbrev_to_us_state[state]} are {', '.join(self._representatives)}")

        # Get the governors
        governorURL = "https://ballotpedia.org/List_of_governors_of_the_American_states"
        governorData = pd.read_html(governorURL)[1]
        self._governor = \
        governorData[governorData.stack().str.contains(abbrev_to_us_state[state]).groupby(level=0).any()][
            "Name"].to_list()
        self._l.debug(
            f"The governor of {abbrev_to_us_state[state]} is {', '.join(self._governor)}")

        # Get the list of questions and answers
        self.getQuestionsandAnswers()
        self.getQuestionsandAnswersUpdates()
        self._l.debug(f"Got {len(self.questions)} questions from online")

        # Augment the answers to be specific to updates and for a state
        self.stateSpecific = []
        for i, question in enumerate(self.questions):
            if "Senators now" in question:
                try:
                    self.answers[i] = self._senators
                except:
                    self.answers[i] = [f"Trick question. {self._state} isn't a state"]
                self.stateSpecific.append(f"Updated for {self._state} on {date.today()}")

            elif "your U.S. Representative" in question:
                self.answers[i] = self._representatives
                self.stateSpecific.append(f"Updated for {self._state} on {date.today()}")

            elif "Governor of your state" in question:
                try:
                    self.answers[i] = self._governor
                except:

                    self.answers[i] = [f"Trick question. {self._state} doesn''t have a Gov."]

                self.stateSpecific.append(f"Updated for {self._state} on {date.today()}")

            elif "capital of your state" in question:
                try:
                    self.answers[i] = [stateDict[abbrev_to_us_state[self._state]]]
                except:
                    self.answers[i] = ["Trick question. DC isn't a state"]

            elif "Answers will vary" in self.answers[i][0]:
                self.answers[i] = self.answerUpdateDict[i + 1]
                self.stateSpecific.append(f"Updated on {date.today()}")

            elif "Visit" in self.answers[i][0]:
                self.answers[i] = self. answerUpdateDict[i+1]
                self.stateSpecific.append(f"Updated on {date.today()}")
            else:
                self.stateSpecific.append("")

        # Write the flashcard latex
        self.writeFlashCards()

        # Run the latex
        os.system("pdflatex latexFile.tex")

        # Move the output
        fromFile = "latexFile.pdf"
        toFile = f"flashCards/USCIS_CitizenshipTest_2008_FlashCards_{abbrev_to_us_state[self._state]}.pdf"
        os.rename(fromFile, toFile)

    def writeFlashCards(self):

        texHeader = r"""\documentclass[avery5371,frame]{flashcards}
        \usepackage{graphicx,xcolor}
        \usepackage{mhchem}

        \cardfrontstyle{headings}

        \begin{document}"""

        texFooter = r"""\end{document}"""

        def texFlash(i, topLeft, question, answer):
            theTex = f"""\\cardfrontfoot{{Question {i}}}
        \\begin{{flashcard}}[\\tiny {topLeft}]{{{question}}}
        {{{answer}}}
        \\end{{flashcard}}"""
            return theTex

        with open("latexFile.tex", "wt") as f:
            f.write(texHeader)

            for i, (q, a, g, s, ss) in enumerate(zip(self.questions, self.answers,
                                                 self.groups, self.subcategories,
                                                 self.stateSpecific)):


                if len(a) == 0:
                    answers = ""
                elif len(a) < 8:
                    answers = "\\\\".join(a)
                else:
                    answers = "\\footnotesize, ".join(a[0:20])
                    if len(a) > 20:
                        answers += f"...and {len(a)-20} more"
                if not ss == "":
                    try:
                        answers += f"{{\\footnotesize{{\\textsl{{{ss}}}}}}}"
                    except:
                        answers += f"{{\\footnotesize{{\\textsl{{{ss}}}}}}}"

                print(answers)
                thisTex = texFlash(i + 1, f"{g}: {s}", q, answers.replace(r'[', r'\[').replace(r']', r'\]'))
                f.write(thisTex)

            f.write(texFooter)

    def getQuestionsandAnswers(self):
        url = "https://www.uscis.gov/citizenship/find-study-materials-and-resources/study-for-the-test/100-civics-questions-and-answers-with-mp3-audio-english-version"
        html = urlopen(url).read()
        soup = BeautifulSoup(html, features="html.parser")

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()  # rip it out

        # get text
        text = soup.get_text()

        # break into lines and remove leading and trailing space on each
        lines = [line.strip() for line in text.splitlines()]
        # break multi-headlines into a line each
        chunks = [phrase.strip() for line in lines for phrase in line.split("  ")]
        # drop blank lines
        text = ['\n'.join(chunk for chunk in chunks if chunk)]

        theLines = text[0].split("\n")

        regexp = re.compile(r"[1234567890]\. ")

        self.questions = []
        self.answers = []
        self.groups = []
        self.subcategories = []

        groupList = ["AMERICAN GOVERNMENT",
                     "AMERICAN HISTORY",
                     "INTEGRATED CIVICS"]

        subcategoryList = ["A: Principles of American Democracy",
                           "B: System of Government",
                           "C: Rights and Responsibilities",
                           "A: Colonial Period and Independence",
                           "B: 1800s",
                           "C: Recent American History and Other Important Historical Information",
                           "A: Geography",
                           "B: Symbols",
                           "C: Holidays"]

        def split_str(str):
            ref_dict = {
                '\x07': 'a',
                '\x08': 'b',
                '\x0C': 'f',
                '\n': 'n',
                '\r': 'r',
                '\t': 't',
                '\x0b': 'v',
                '\xa0': 'p'
            }
            res_arr = []
            temp = ''
            for i in str:
                if not i == '\\':
                    if i in ref_dict:
                        if not temp == "":
                            res_arr.append(temp)
                        res_arr.append(ref_dict[i])
                        temp = ''
                    else:
                        temp += i
                else:
                    if not temp == '':
                        res_arr.append(temp)
                    temp = ''
            res_arr.append(temp)
            return res_arr

        atEnd = False
        for eachLine in theLines:

            if not atEnd:
                header = False

            if eachLine in groupList:
                theGroup = eachLine
                header = True
            elif eachLine in subcategoryList:
                theSubcategory = eachLine
                header = True

            if "Last Reviewed" in eachLine:
                atEnd = True
                header = True

            if (regexp.search(eachLine)) and not ("mp3" in eachLine.lower()):
                self.questions.append((split_str(eachLine)[0]).split(" Question")[0])
                if (len(self.questions) > 1) and not header:
                    self.answers.append(theseAnswers)

                theseAnswers = []

                self.groups.append(theGroup)
                self.subcategories.append(theSubcategory)
            elif (len(self.questions) > 0) and not ("mp3" in eachLine.lower()) and not header:
                theseAnswers.append(eachLine)

        self.answers.append(theseAnswers)

    def getQuestionsandAnswersUpdates(self):
        url = "https://www.uscis.gov/citizenship/find-study-materials-and-resources/check-for-test-updates"
        self.updateURL = url
        html = urlopen(url).read()
        soup = BeautifulSoup(html, features="html.parser")

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()  # rip it out

        # get text
        text = soup.get_text()

        # break into lines and remove leading and trailing space on each
        lines = [line.strip() for line in text.splitlines()]
        # break multi-headlines into a line each
        chunks = [phrase.strip() for line in lines for phrase in line.split("  ")]
        # drop blank lines
        text = ['\n'.join(chunk for chunk in chunks if chunk)]

        theLines = text[0].split("\n")

        regexp = re.compile(r"[1234567890]\. ")

        questionUpdates = []
        answerUpdates = []

        def split_str(str):
            ref_dict = {
                '\x07': 'a',
                '\x08': 'b',
                '\x0C': 'f',
                '\n': 'n',
                '\r': 'r',
                '\t': 't',
                '\x0b': 'v',
                '\xa0': 'p'
            }
            res_arr = []
            temp = ''
            for i in str:
                if not i == '\\':
                    if i in ref_dict:
                        if not temp == "":
                            res_arr.append(temp)
                        res_arr.append(ref_dict[i])
                        temp = ''
                    else:
                        temp += i
                else:
                    if not temp == '':
                        res_arr.append(temp)
                    temp = ''
            res_arr.append(temp)
            return res_arr

        self.answerUpdateDict = {}
        atEnd = False
        for eachLine in theLines:

            if not atEnd:
                header = False
            else:
                header = True

            if "2020 Civics" in eachLine:
                atEnd = True
                answerUpdates.append(theseAnswers)

            if (not atEnd) and (regexp.search(eachLine)) and not ("mp3" in eachLine.lower()):

                questionUpdates.append((split_str(eachLine)[0]).split(" Question")[0])
                if (len(questionUpdates) > 1) and not header:
                    answerUpdates.append(theseAnswers)

                theseAnswers = []

                questionNumber = int(eachLine.split('.')[0])



            elif (len(questionUpdates) > 0) and not ("mp3" in eachLine.lower()) and not header:
                theseAnswers.append(eachLine)

                self.answerUpdateDict[questionNumber] = theseAnswers

    def _get_logger(self, logLevel="WARN"):
        """
        Makes a logger that only sets handlers once

        :param logLevel:
        :return:
        """

        logging.shutdown()
        l = logging.getLogger(__name__)
        l.handlers.clear()

        # Clear existing loggers
        try:
            os.remove("flashCard.log")
        except:
            pass

        if not getattr(l, "hander_set", None):
            # Make a handler for streaming to console - this will only print out messages at the level
            # requested
            h = logging.StreamHandler()
            f = logging.Formatter('%(funcName)s %(asctime)s %(levelname)s: %(message)s')
            h.setLevel(logLevel)
            h.setFormatter(f)
            l.removeHandler(h)
            l.addHandler(h)

            # And a separate logger to
            h = logging.FileHandler("flashCard.log")
            f = logging.Formatter('%(funcName)s %(asctime)s %(levelname)s: %(message)s')
            h.setLevel(logging.DEBUG)
            h.setFormatter(f)
            l.removeHandler(h)
            l.addHandler(h)

            l.handler_set = True

        return l



if __name__ == "__main__":

    for i, eachState in enumerate(abbrev_to_us_state.keys()):

        logging.shutdown()
        # Make a flashcard Object
        myCards = flashCards(eachState, logLevel="DEBUG")
        myCards._l.handlers.clear()
        logging.shutdown()



