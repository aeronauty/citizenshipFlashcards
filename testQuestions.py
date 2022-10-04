from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

url = "https://www.uscis.gov/citizenship/find-study-materials-and-resources/study-for-the-test/100-civics-questions-and-answers-with-mp3-audio-english-version"
html = urlopen(url).read()
soup = BeautifulSoup(html, features="html.parser")

# kill all script and style elements
for script in soup(["script", "style"]):
    script.extract()    # rip it out

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

questions = []
answers = []
groups = []
subcategories = []

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
        '\x07':'a',
        '\x08':'b',
        '\x0C':'f',
        '\n':'n',
        '\r':'r',
        '\t':'t',
        '\x0b':'v',
        '\xa0':'p'
    }
    res_arr = []
    temp = ''
    for i in str :
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
        questions.append((split_str(eachLine)[0]).split(" Question")[0])
        if (len(questions) > 1) and not header:
            answers.append(theseAnswers)

        theseAnswers = []

        groups.append(theGroup)
        subcategories.append(theSubcategory)
    elif (len(questions) > 0) and not ("mp3" in eachLine.lower()) and not header:
        theseAnswers.append(eachLine)

answers.append(theseAnswers)

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

    for i, (q, a, g, s) in enumerate(zip(questions, answers, groups, subcategories)):

        if "Senators now" in q:
            print(q)

        answers = "\\\\".join(a)
        thisTex = texFlash(i+1, f"{g}: {s}", q, answers.replace(r'[', r'\[').replace(r']', r'\]'))
        f.write(thisTex)

    f.write(texFooter)


