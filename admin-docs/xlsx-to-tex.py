import numpy as np
import pandas as pd
from datetime import datetime
import re

# excel file name, to use in tex file itself
# xlsx_file_name = "MAMEC Curriculum 20250609.xlsx"
# xlsx_file_name = "MAMEC Curriculum 20250609-tbd.xlsx"
# xlsx_file_name = "MAMEC Curriculum (final).xlsx"
# xlsx_file_name = "MAMEC Curriculum (final) 20250620.xlsx"
# xlsx_file_name = "MAMEC Curriculum (final) 20250623.xlsx"
# xlsx_file_name = "MAMEC Curriculum (final) 20250625.xlsx"
xlsx_file_name = "MAMEC Curriculum (final) 20250725.xlsx"

# We capture book titles from reading assignments as we go.
# Should we print a list of them at the end of doc?
booklist_print = False

# read by default 1st sheet of an excel file
# xlsx_df = pd.read_excel("admin-docs/MAMEC Curriculum 20250527.xlsx")
xlsx_df = pd.read_excel("admin-docs/{0}".format(xlsx_file_name))

# print(xlsx_df)

# This is just a big chunk of tex that we want to start the document with, no parsing, hence the raw string prefix 'r'
# NOTE: For now, it is on purpose that the 'Updated:' date variable below is not auto-generated. I only want to change that date when I change the xlsx file, not every time I rerun this script - which might be for formatting changes or things we don't need to issue a full 'revision' for
updated_date = "2025-07-25"

tex_doc_start_1 = r"""
%\DocumentMetadata{}
\documentclass{article}
\usepackage[calc,useregional]{datetime2}
\newcounter{printSessionDate} %creates empty counter/variable for whether or not to print session dates. Do Not Change This.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%         Edit these values
%%

\title{Middle Eastern Classics Reading Lists 2025--2026}
\author{St.\ John's College --- Santa Fe Graduate Institute}
"""

tex_doc_start_date_updated_titlepage = "\\date{{Updated: {}}}".format(updated_date)

tex_doc_start_2 = r"""
\setcounter{printSessionDate}{0}% setting to 0 will not print dates after "Session XYZ", setting to 1 will print dates (e.g. "Session XYZ - 2025-09-09")

\DTMsavedate{fallSeminarStart}{2025-09-01}
\DTMsavedate{preceptorial1Start}{2025-09-02}
\DTMsavedate{preceptorial2Start}{2025-10-29}

\DTMsavedate{springSeminarStart}{2026-01-19}
\DTMsavedate{preceptorial3Start}{2026-01-20}
\DTMsavedate{preceptorial4Start}{2026-03-30}

\DTMsavedate{summerSeminarStart}{2026-06-15}
\DTMsavedate{summerPreceptorialStart}{2026-06-16}

%dates for breaks are inclusive, i.e. there are no classes on start or end dates
\DTMsavedate{thanksgivingBreakStart}{2025-11-26}
\DTMsavedate{thanksgivingBreakEnd}{2025-11-30}
\DTMsavedate{springBreakStart}{2026-03-14}
\DTMsavedate{springBreakEnd}{2026-03-29}
% 2025-12-19 no classes, end of fall semester
% 2026-05-22 no classes, end of spring semester

%%
%%
%%        END: Edit these values
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


% Typeset/compile with XeLaTeX !!!
% why? LaTeX will give errors on the unicode characters. If you must use LaTeX, then you can get around the errors with declarations like the line below (that is commented out/not used currently) with the `\DeclareUnicodeCharacter` command...
%% Examples:
%% \DeclareUnicodeCharacter{1E41}{\d{m}} %produces m with dot below it, not above. It works in pdfLaTeX, but not LuaLaTeX
%% \DeclareUnicodeCharacter{1E41}{\(\dot{m}\)} %works in pdfLaTeX, but not LuaLaTeX


%NOTE: trying to save one date as another doesn't work, need to do this little dance to get it into the right format:
%\DTMsavedate{testDate}{\DTMfetchyear{springStart}-\DTMfetchmonth{springStart}-\DTMfetchday{springStart}}


\usepackage{multicol}
\usepackage{titlesec} % for \titlespacing command

%% Default spacing as said on page 25 of http://mirrors.ctan.org/macros/latex/contrib/titlesec/titlesec.pdf
%% of form `\titlespacing*{⟨command ⟩}{⟨left⟩}{⟨before-sep⟩}{⟨after-sep⟩}[⟨right-sep⟩]`
% \titleformat{\section}
% {\normalfont\Large\bfseries}{\thesection}{1em}{}
% \titleformat{\subsection}
% {\normalfont\large\bfseries}{\thesubsection}{1em}{}
%
% \titlespacing*{\section} {0pt}{3.5ex plus 1ex minus .2ex}{2.3ex plus .2ex}
% \titlespacing*{\subsection} {0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}

%% new formatting and spacing to apply to this document
\titleformat{\section}
{\centering\normalfont\LARGE\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}
{\normalfont\large\bfseries}{\thesubsection}{1em}{}
\titlespacing*{\section} {0pt}{3.5ex plus 1ex minus 0.2ex}{1.0ex plus 0.2ex}
\titlespacing*{\subsection} {0pt}{2.75ex plus 1ex minus 0.2ex}{0.75ex plus 0.2ex}

% From http://tex.stackexchange.com/questions/34040/graphics-logo-in-headers
\usepackage{geometry}
%\geometry{letterpaper, margin=0.75in, headsep=15pt}
\geometry{letterpaper, margin=0.75in, headsep=-35pt}
\addtolength{\topmargin}{-50pt}


\usepackage{setspace}

% Insert header image
\usepackage{graphicx}
\usepackage{fancyhdr} % https://www.overleaf.com/learn/latex/Headers_and_footers#Using_the_fancyhdr_package
\pagestyle{fancy}
\fancyhead{} % This is the text to show in the header, right now we want none
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\setlength\headheight{144.0pt}
\addtolength{\textheight}{-94.0pt}
%\setlength\headheight{92.0pt}
%\addtolength{\textheight}{-92.0pt}
\chead{\includegraphics[width=\textwidth]{header-blank.png}}


% Tex automatically adds numbers to the beginning of typset sections, subsections, etc (e.g. the header for each assignment would be: "1.3 Session 3") but we don't want this, so setting this to 0 to stop that
\setcounter{secnumdepth}{0}

% only show first level of sections in Table of Contents (i.e. only `\section{}` commands)
\setcounter{tocdepth}{1}

% how far apart do we want the columns?
\setlength{\columnsep}{1cm}

% run this at begin of document, so they exist. overwrite currentClassDate later, prob with one of the fall/spring/summer-start dates.
\newcount\myNextClassRegister%
\newcounter{dateChanged}
\DTMsavenow{currentClassDate}
\DTMsavenow{lastPrintedClassDate}

% NOTE: "<dow> is the day of the week number starting from 0 for Monday"

%% code/section flow: 
%
%pass in date of last class (that was just printed), 
%get the next class day with \getNextBiweeklyClassDate, 
%then check to make sure the next class day is not during a break
%	if no, cool, print it.
%	if yes, ugh:
%		hand back last day of break for which the previously computed 'next class' date was. We say that the break dates are inclusive, so just pass the last day of break to the \getNextBiweeklyClassDate command and we should be good. then print that new date.

% function - \printHeaderForNextSeminarClassDate: helper function that just runs `\checkIfHoliday{#1}` and then with output, runs `\getNextBiweeklyClassDate{#1}{0}{3}` so that user doesn't need to know about the 0=Monday and 3=Thursday nomenclature.
\newcommand{\printHeaderForNextSeminarClassDate}[1]{%
  % save input to tempDate variable, don't really need to but looks prettier for code?
  \DTMsavedate{tempDate}{\DTMfetchyear{#1}-\DTMfetchmonth{#1}-\DTMfetchday{#1}}%
  % make sure dateChanged counter = 0 to properly record if any changes happen
  \setcounter{dateChanged}{0}%

  %test%\DTMusedate{currentClassDate}%
  \getNextBiweeklyClassDate{0}{3}{tempDate}%
  % \getNextBiweeklyClassDate{0}{3}{#1}%

  \checkIfDateIsBetweenSchoolBreaks{tempDate}%

  % check if date was changed
  \ifnum\value{dateChanged}>0%
    %date was changed, so now get next class day after
    \getNextBiweeklyClassDate{0}{3}{tempDate}%
  \fi%

  %now pass that date on to be printed out
  \printHeaderWithSessionAndDate{tempDate}%
}


% function - \printHeaderForNextPreceptorialClassDate: helper function that just runs `\checkIfHoliday{#1}` and then with output, runs `\getNextBiweeklyClassDate{#1}{1}{3}` so that user doesn't need to know about the 1=Tuesday and 3=Thursday nomenclature.
\newcommand{\printHeaderForNextPreceptorialClassDate}[1]{%
  % save input to tempDate variable, don't really need to but looks prettier for code?
  \DTMsavedate{tempDate}{\DTMfetchyear{#1}-\DTMfetchmonth{#1}-\DTMfetchday{#1}}%
  % make sure dateChanged counter = 0 to properly record if any changes happen
  \setcounter{dateChanged}{0}%

  \getNextBiweeklyClassDate{1}{3}{tempDate}%

  \checkIfDateIsBetweenSchoolBreaks{tempDate}%

  % check if date was changed
  \ifnum\value{dateChanged}>0%
    %date was changed, so now get next class day after
    \getNextBiweeklyClassDate{1}{3}{tempDate}%
  \fi%

  %now pass that date on to be printed out
  \printHeaderWithSessionAndDate{tempDate}%
}


%\getNextBiweeklyClassDate: pass in <DoW of 1st class day>, <DoW of 2nd class day>, and <a Date for which you want to know the next class Date on the appropriate DoW>
% e.g. :
%    \DTMsavedate{fallStart}{2024-09-02} % Note: a monday
%    Usage: type in document `\getNextBiweeklyClassDate{0}{3}{fallStart}`
%        Notes: 0 and 3 indicate classes are Monday (0), and Thursday (3).tempDate
%    Function Result: In above example, saves the date of "2024-09-05" (because that is the Thursday after the Monday provided) to the variable `currentClassDate` (equivalent to running `\DTMsavedate{currentClassDate}{2024-09-05}`)
\newcounter{DoWfirst}%
\newcounter{DoWsecond}%
\newcounter{daysToAdvance}%
\newcommand{\getNextBiweeklyClassDate}[3]{%
  % put DoW for classes in order, in case user inputs {3}{0}{date}
  \ifnum#1<#2%
    \setcounter{DoWfirst}{#1}%
    \setcounter{DoWsecond}{#2}%
  \else%
    \setcounter{DoWfirst}{#2}%
    \setcounter{DoWsecond}{#1}%
  \fi%

  %figure out how many days to advance any date to get the next biweekly class DoW date
  \ifnum\DTMfetchdow{#3}<\value{DoWfirst}%
    % increment date to DoW of DoWfirst
    \DTMsaveddateoffsettojulianday{#3}{\numexpr\value{DoWfirst}-\DTMfetchdow{#3}}{\myNextClassRegister}%
    \DTMsavejulianday{tempDate}{\number\myNextClassRegister}%
  \else%
    \ifnum\DTMfetchdow{#3}<\value{DoWsecond}% %i.e. DoW of currentClassDate is NOT less than DoWfirst, and IS less than DoWsecond
      % increment date to DoW of DoWsecond
      \DTMsaveddateoffsettojulianday{#3}{\numexpr\value{DoWsecond}-\DTMfetchdow{#3}}{\myNextClassRegister}%
      \DTMsavejulianday{tempDate}{\number\myNextClassRegister}%
    \else% %i.e. DoW of currentClassDate is NOT less than DoWfirst, and is NOT less than DoWsecond
      %advance the date to next DoWfirst after date's DoW
      %\the\numexpr(7+\value{DoWfirst}-\DTMfetchdow{#3})
      \setcounter{daysToAdvance}{\numexpr(7+\value{DoWfirst}-\DTMfetchdow{#3})}%
      \DTMsaveddateoffsettojulianday{#3}{\value{daysToAdvance}}{\myNextClassRegister}%
      \DTMsavejulianday{tempDate}{\number\myNextClassRegister}%
    \fi%
  \fi%
}


%function - \checkBreakRanges: takes in a date and the two Days of the week that a class is held on, check if date is between the defined school breaks.
% returns nothing, but will change value of `tempDate` and `dateChanged` if needed.
\newcommand{\checkIfDateIsBetweenSchoolBreaks}[1]{%
  % check if date passed in is between two defined schools breaks
  \checkIfDateBetweenDates{tempDate}{thanksgivingBreakStart}{thanksgivingBreakEnd}%
  \checkIfDateBetweenDates{tempDate}{springBreakStart}{springBreakEnd}%
}


%function - \checkIfDateBetweenDates: this command will check if a date is between two dates (inclusively). If it is not, function does nothing. If it is between the two dates, this function will write a header of "No Classes from <first-date-in-range> - <last-date-in-range>" and then set a counter to mark that the date is change, and change the value of `tempDate` to <last-date-in-range>.
% parameters: \checkIfDateBetweenDates{<date-to-check>}{<first-date-in-range>}{<last-date-in-range>}
\newcommand{\checkIfDateBetweenDates}[3]{%
  \DTMifdate{#1}
  {between=
  \DTMfetchyear{#2}-\DTMfetchmonth{#2}-\DTMfetchday{#2}
  and
  \DTMfetchyear{#3}-\DTMfetchmonth{#3}-\DTMfetchday{#3}
  } {\DTMsavedate{tempDate}{\DTMfetchyear{#3}-\DTMfetchmonth{#3}-\DTMfetchday{#3}} \setcounter{dateChanged}{1} \subsection{\emph{No Classes:} \DTMusedate{#2}--\DTMusedate{#3}}\vspace{0.4cm}}{}
}


%function - \printHeaderWithSessionAndDate: increments countSession (since it starts at 0), then prints text for Session <countSession> - <currentClassDate> 
\newcommand{\printHeaderWithSessionAndDate}[1]{%
	\stepcounter{countSession}%
	\subsection{Session \arabic{countSession} - \DTMusedate{#1}}%

  % save date we just printed into lastPrintedClassDate to pass on to next header printing
  \DTMsavedate{lastPrintedClassDate}{\DTMfetchyear{#1}-\DTMfetchmonth{#1}-\DTMfetchday{#1}}
}


%function - \printHeaderWithSession: increments countSession (since it starts at 0), then prints text for Session <countSession>
% just in case one doesn't want the dates that I wrote so much code to calculate... Don't use this function and \printHeaderWithSessionAndDate in same doc, it will prob mess up counters/registers
\newcommand{\printHeaderWithSession}{%
	\stepcounter{countSession}%
	\subsection{Session \arabic{countSession}}%
}


%function - \printPreceptorialHeader: checks variable to see if we should print a header with just session, or also with date - then runs appropriate function
\newcommand{\printPreceptorialHeader}[1]{	
	% check if we should print dates or not
	\ifnum\value{printSessionDate}=0% nope!
		\printHeaderWithSession%
	\else% yep!
		\printHeaderForNextPreceptorialClassDate{#1}
	\fi
}

%function - \printSeminarHeader: checks variable to see if we should print a header with just session, or also with date - then runs appropriate function
\newcommand{\printSeminarHeader}[1]{	
	% check if we should print dates or not
	\ifnum\value{printSessionDate}=0% nope!
		\printHeaderWithSession%
	\else% yep!
		\printHeaderForNextSeminarClassDate{#1}
	\fi
}


% set counter/variable to keep track of which week it is
\newcounter{countSemester} % mostly used to reset class session counter
\newcounter{countSession}
\counterwithin{countSession}{countSemester}

%\usepackage{transparent}% if you want to typeset transparent text, also uncomment the line at top of file `\DocumentMetadata{}`
\usepackage{xcolor}  

% Load this package last?!
\usepackage{hyperref} % make clickable links, e.g. for table of contents https://www.overleaf.com/learn/latex/Hyperlinks

%% make links a color
%\hypersetup{
%  colorlinks   = true, %Colours links instead of ugly boxes
%  urlcolor     = blue, %Colour for external hyperlinks
%  linkcolor    = blue, %Colour of internal links
%  citecolor   = red %Colour of citations
%}

%% underline the black text links with colored line
%% NOTE: underlined links in PDFs do not show up in chrome PDF viewer, it is a known bug that is not getting fixed. The underlinging does show in Firefox browser and Adobe Acrobat viewers.
\hypersetup{%
    pdfborderstyle={/S/U/W 1}, % underline links instead of boxes
    linkbordercolor=red,       % color of internal links
    citebordercolor=green,     % color of links to bibliography
    filebordercolor=magenta,   % color of file links
    urlbordercolor=cyan        % color of external links
}

% Add Section name to header text
\fancyhead[R]{%
\huge\textbf{\textcolor{white}{Middle Eastern Classics~~\\\nouppercase{\leftmark}}}
\vspace{26mm}
}
\fancyheadwidth[R][cc]{0.55\headwidth}
% the two ~~ are there to get centering closer to correct looking.


% End - Introductory typesetting configuration


%%%
%%%%% Begin Main Document
%%%

\begin{document}


\maketitle

\renewcommand*\contentsname{Reading Lists}
\tableofcontents

%\vspace{2cm}
%\textit{\textbf{Note}: For the spring term, students will be provided with a list of options for preceptorials.}

\thispagestyle{fancy} % instead of a `plain` pagestyle this set it to a style which includes the header on the Table of Contents page
%\thispagestyle{empty} %use this instead of above 'fancy' line, if you do not want a header image on the first page of this document

"""

tex_doc_start_date_updated_footer = """\\fancyfoot[R]{{\\textit{{Updated: {}}}}}
""".format(
    updated_date
)

tex_section_classes_start = r"""
\begin{multicols}{2}
%\begin{multicols*}{2} % uncomment this line and the matching begin or end line if columns are divided oddly on the last page of this section
    %\raggedcolumns

"""

tex_section_classes_end = r"""
\end{multicols}
%\end{multicols*} % uncomment this line and the matching begin or end line if columns are divided oddly on the last page of this section
"""

# TODO: instead of compressing all text, just change spacing between class sections. with variable set per section? another way?
tex_section_classes_condensed_start = r"""    \begin{spacing}{0.98}
    
"""

tex_section_classes_condensed_end = r"""    \end{spacing}
"""

tex_booklist_start = r"""
\end{multicols}
%\end{multicols*} % uncomment this line and the matching begin or end line if columns are divided oddly on the last page of this section


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%                              %%
%%          Book List           %%
%%                              %%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%page break
\clearpage

\begin{center}
	\section{Book List}
\end{center}

Books are listed in the order in which they are encountered in class.

\begin{multicols}{2}
%\begin{multicols*}{2} % uncomment this line and the matching begin or end line if columns are divided oddly on the last page of this section
"""

tex_doc_end_MAMEC = r"""
\end{multicols}
%\end{multicols*} % uncomment this line and the matching begin or end line if columns are divided oddly on the last page of this section
% TODO: add QR code to some survey/form through which people can easily submit changes/errors/etc?
% TODO: add QR to online HTML version??

\end{document}
"""


# create a file name output-DATE-TIME.tex for writing and write into it with below code
# loop through all rows of xlsx_df. if column 1 has word "PRECEPTORIAL" or "SEMINAR" in it, print this string "\begin{center}\n	\section[CELL_CONTENTS]{CELL_CONTENTS}\n\end{center}" where CELL_CONTENTS is the contents of first cell and save contents of first cell to variable named SECTIONAME.
# Then continue to next row.
# If row's first cell does not contain those strings from above, then do this: if variable SECTIONAME contains SEMINAR, print the command to make a seminar header (`\printSeminarHeader{lastPrintedClassDate}`), else print the command to make a precept header (`\printPreceptorialHeader{lastPrintedClassDate}`). Then print reading assignment as tex for that subsection.


tex_section_header_start = """
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
%%
%%         {0}
%%
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% date dancing, don't change - this gives us the day before the first day of classes
%WHY?? well then all the function calls to print the session header below can be the same... confusing? a little, but hopefully void future errors in user-editable section below.
\\DTMsavedate{{lastPrintedClassDate}}{{\\DTMfetchyear{{{1}Start}}-\\DTMfetchmonth{{{1}Start}}-\\numexpr\\DTMfetchday{{{1}Start}}-1}}
% End - 'don't change' section {1} test of lower and remove spaces

%page break
\\clearpage

% increment semester count
\\stepcounter{{countSemester}}

"""


# ok this has become more of 'escapeAndCorrectTex'...
def escape_tex(input_str):
    """Escape TeX special characters in a given string."""
    tex_special_chars_regex = r"([#\$%\&\_\\{\}\~\^])"
    escaped_str = re.sub(tex_special_chars_regex, r"\\\1", input_str)
    escaped_str = escaped_str.replace("\u2013", "-")
    # undo english--only to english-only
    # escaped_str = re.sub(r"(\w)--(\w)", r"\1-\2", escaped_str, flags=re.U)
    # escaped_str = escaped_str.replace("-", "--")
    escaped_str = escaped_str.replace("\u00A0", " ")

    # deal with unicode quotes: “”
    escaped_str = escaped_str.replace("\u201c", "``")
    escaped_str = escaped_str.replace("\u201d", "''")

    # replace double quotes with tex-style quotes
    escaped_str = re.sub('"(.*)"', r"``\1''", escaped_str)

    # convert to double dashes and remove spaces from 80 -- 90 or 80-- 90 or 80- 90 or 80-90 etc.
    # also: ] - S -> ]--S
    escaped_str = re.sub(r"([\d\]])\s*-{1,2}\s*([\dS])", r"\1--\2", escaped_str)
    # also roman numerals
    escaped_str = re.sub(r"([IVXLC])\s*-{1,2}\s*([IVXLC])", r"\1--\2", escaped_str)

    ## ok and now special cases - you shoudl prob always look to see if these are still needed if any content changed (and thus text may fit onto the line differently)
    # help tex not make weird underfull hbox spacing, replace Suhrawardi's Introduction with Suhra\-wardi's Introduction
    escaped_str = escaped_str.replace(
        "Suhrawardī's Introduction", "Suhra\\-wardī's Introduction"
    )

    ## Changed in xlsx file on OneDrive
    # escaped_str = escaped_str.replace(
    #     r"(Parens and Macfarland), pp. 162--179)",
    #     r"(Parens and Macfarland, pp. 162--179)",
    # )

    # # Spring Seminar Session 16, make it split onto a new page more nicely
    # escaped_str = escaped_str.replace(
    #     "pp.311--316; First Discussion - The denial",
    #     "pp.311--316; (\\emph{Readings continued on next page})\n\n    \\noindent First Discussion - The denial",
    # )

    # replace ’s with 's for tex typsetting
    escaped_str = escaped_str.replace(r"’s ", r"'s ")

    # replace s’ with s' for tex typsetting
    escaped_str = escaped_str.replace(r"s’ ", r"s' ")

    # replace don’t with don't for tex typsetting
    escaped_str = escaped_str.replace(r"don’t", r"don't")

    # … replace horizontal ellipsis with tex-dots
    escaped_str = escaped_str.replace("\u2026", r"\(\ldots\)")
    # replace ... with \ldots
    escaped_str = escaped_str.replace("...", r"\(\ldots\)")

    # Wrap hyperlinks in \url{} command, which then manages line breaks and style
    escaped_str = re.sub(r"http(\S*)/", r"\\url{http\1/}", escaped_str)
    # or could do a directly negated whitespace class if we also want to add other characters to not match, like `([^\s{}]*)`

    # just special case this one
    escaped_str = escaped_str.replace(
        r"www.youtube.com/watch?v=2lgNAOFIJig",
        r"\url{www.youtube.com/watch?v=2lgNAOFIJig}",
    )

    return escaped_str


# what characters are used in the spreadsheet to mark separation between book titles?
book_split_regex = "[;&]"

# Initialize Values
# class_type = "Seminar"
# class_name = "Fall Seminar"
class_sessions_counter = 0
books_dict = dict()

# NOTE: use `\-` to give latex hints at where to breaks words if you gt under/over-full hbox warnings


# Make column names into vars
col_books = "Book Names (To Italicize)"
col_week = "Week"
col_reading = "Reading Assignment"

# Prob don't use this but we'll see
col_names = xlsx_df.columns

url_repo_script = (
    r"https://github.com/julowe/st-johns/blob/main/admin-docs/xlsx-to-tex.py"
)

url_binder_typeset = r"https://mybinder.org/v2/gh/julowe/binder-reading-lists/HEAD?urlpath=%2Fdoc%2Ftree%2Findex.ipynb"

typset_dtm = datetime.now().strftime("%Y-%m-%dT%H:%M")

## Not used.
# ugly bc to make \\ we need to escape both, so \\\\. and I do want the indents in the tex file, for readability.
how_to_string = """\n\n\\begin{{center}}
    \\texttransparent{{0}}{{%
        This document typeset by: \\\\
        {0} \\\\
        on {1} \\\\
        from `{2}' \\\\
        by Justin Lowe.
    }}
\\end{{center}}
""".format(
    url_repo_script,
    typset_dtm,
    xlsx_file_name,
)

class_name = None
with open(
    "admin-docs/tex-output-test/output-{0}.tex".format(typset_dtm),
    "w",
) as f:
    # write header on what file we used to generate this
    f.write(
        "% Generated by {0} on {1} from '{2}' by Justin Lowe. \n% Or use this binder notebook to upload an xlsx file and typeset it yourself: {3} \n".format(
            url_repo_script, typset_dtm, xlsx_file_name, url_binder_typeset
        )
    )

    # write all the user-editable variables and functions before actual content
    f.write(tex_doc_start_1)
    f.write(tex_doc_start_date_updated_titlepage)
    f.write(tex_doc_start_2)
    f.write(tex_doc_start_date_updated_footer)

    ## In the end, not used. Can't be sure transparency will really work with all printers etc. Need better way to unobtrusively indicate how to make this doc again...
    # write transparent text to point to how to typeset this doc and the code to do so
    # f.write(how_to_string)

    for index, row in xlsx_df.iterrows():
        # Check if this is a 'section' type row
        if isinstance(row[col_week], str):
            if "LANGUAGE" in row[col_week].upper():
                class_name = row[col_week].title().strip()

                # create a new dict entry for books to be added to
                books_dict[class_name] = []

            if (
                "PRECEPTORIAL" in row[col_week].upper()
                or "SEMINAR" in row[col_week].upper()
            ):
                # NOTE: run this check before we change the class_name variable from last run through
                if class_name:
                    if class_name == "Spring Seminar":
                        f.write(tex_section_classes_condensed_end)

                class_name = row[col_week].title().strip()
                class_name_camelCase = class_name[0].lower() + class_name[1:].replace(
                    " ", ""
                )

                # create a new dict entry for books to be added to
                books_dict[class_name] = []

                # Check if class session counter is greater than 0, if so we are going to a new section and need to close out the previous one
                if class_sessions_counter > 0:
                    f.write(tex_section_classes_end)

                # reinitialize class session counter
                class_sessions_counter = 0

                f.write(
                    tex_section_header_start.format(class_name, class_name_camelCase)
                )

                if "PRECEPTORIAL" in row[col_week]:
                    class_type = "Preceptorial"

                    if "1" in row[col_week] or "3" in row[col_week]:
                        section_ordinal = "First"
                    elif "2" in row[col_week] or "4" in row[col_week]:
                        section_ordinal = "Second"

                    if "1" in row[col_week] or "2" in row[col_week]:
                        section_semester = "Fall"
                    elif "3" in row[col_week] or "4" in row[col_week]:
                        section_semester = "Spring"

                    # write the section header
                    # NOTE: a double {{ is how to make it print a single {
                    f.write(
                        "\\section[{0}]{{{0}}}\n\\begin{{center}}\n      \\vspace{{-0.5ex}}\n    ({1} Eight Weeks of {2})\n\\end{{center}}\n".format(
                            class_name, section_ordinal, section_semester
                        )
                    )
                else:
                    class_type = "Seminar"
                    f.write("\\section{{{0}}}".format(class_name))

                # If this was a 'section' type header then don't need to do anything else, go to next row
                continue
            elif "WEEK" in row[col_week].upper():
                # record the week number, in case we need it later
                week_number = row[col_week]
                # If this had a week number we want to process it. continue on.

        # Check if this row has a book assignment in it
        if isinstance(row[col_books], str):
            if "LANGUAGE" in class_name.upper():
                # Build up a booklist as we go
                # see if there are multiple books here
                row_book_array = re.split(book_split_regex, row[col_books])
                # print(row_book_array)

                for book in row_book_array:
                    if escape_tex(book.strip()) not in books_dict[class_name]:
                        books_dict[class_name].append(escape_tex(book.strip()))

                # ok we added language book to the book list, we didn't make a section for them and no reading assignments to print, so bounce.
                continue

            # check if this is a holiday or other weird row with no reading assignment in it
            if isinstance(row[col_reading], str):
                # normal row, make a subsection entry - NB: some of the \ characters are escaped (with a \), the newline (\n) is not

                # Apparently one of the Thanksgiving rows gets read in as having a space. None in online xlsx file do...
                if row[col_reading] == " ":
                    continue
                # print("Book: '{0}', Reading Assignment: '{1}'".format(row[col_books],row[col_reading]))

                if class_sessions_counter == 0:
                    f.write(tex_section_classes_start)
                    if class_name:
                        if class_name == "Spring Seminar":
                            f.write(tex_section_classes_condensed_start)

                # not used now, but may be useful later - prob not, to make it easier to make small text changes we prob want the tex file we create here to be standalone on overleaf or a desktop tex instance. so leave data and sessio math to the tex file...
                class_sessions_counter += 1

                # Build up a booklist as we go
                # see if there are multiple books here (and replace new-lines with semicolons)
                # row_book_array = re.split(
                #     book_split_regex, row[col_books].replace("\n", "; ")
                # )

                row_book_array = [
                    x.strip() for x in re.split(book_split_regex, row[col_books])
                ]

                # string = "  blah, lots  ,  of ,  spaces, here "
                # pattern = re.compile("^\s+|\s*,\s*|\s+$")
                # print([x for x in pattern.split(string) if x])

                for book in row_book_array:
                    if escape_tex(book.strip()) not in books_dict[class_name]:
                        books_dict[class_name].append(escape_tex(book.strip()))

                ## construct reading assignment string
                # Get initial string
                string_reading = row[col_reading].strip().replace("\n", "; ")

                # Escape odd characters
                string_reading = escape_tex(string_reading)

                # italicize book names
                # if member of row_book_array is in string string_reading, then enclose that substring in tex italics

                # TODO: needed?
                # Sort book titles by length (descending) to handle cases where one title is subset of another
                sorted_books = sorted(row_book_array, key=len, reverse=True)

                # Iterate through each book title
                for book in sorted_books:
                    # Escape any special LaTeX characters in the book title
                    book_escaped = escape_tex(
                        book
                    )  # TODO i think this is already escaped

                    # Replace the book title with its italicized version if found in the string
                    string_reading = string_reading.replace(
                        book_escaped, "\\textit{{{0}}}".format(book_escaped)
                    )

                # construct and write actual text for session's assignment
                f.write(
                    "    \\print{0}Header{{lastPrintedClassDate}}\n	{1}\n\n".format(
                        class_type,
                        string_reading,
                    )
                )

            ## Saving this code for later in case useful, but no prob want to leave this logic for tex file. though it might be useful for catching weirdnesses like the " " in that one Thanksgiving row...
            # else:
            #     # holiday or weird row
            #     if "THANKSGIVING" in row[col_books].upper():
            #         # oh actually do nothing, this is handled by TeX functions. for now, maybe move all that mess here?
            #     if "SPRING BREAK" in row[col_books].upper():
            #         # oh actually do nothing, this is handled by TeX functions. for now, maybe move all that mess here?

    ## Not needed if we are adding a book list
    # # Check if class session counter is greater than 0, if so we are going to a new section and need to close out the previous one
    # if class_sessions_counter > 0:
    #     f.write(tex_section_classes_end)

    if booklist_print:

        f.write(tex_booklist_start)

        for semester in books_dict:
            # print(semester)
            f.write(
                "\n\\subsection{{{0} Books}}\n\\begin{{itemize}}\n".format(semester)
            )
            for book in books_dict[semester]:
                # print(book)
                f.write("    \\item {0}\n".format(book))

            f.write("\\end{itemize}\n")
        # TODO: write booklist as separate tex file?

    # all done, write closing code for tex file
    f.write(tex_doc_end_MAMEC)


## code/text not used below this comment...

tex_doc_end_MAEC = r"""

TODO?? Or is this even useful??

\subsection{Eastern Classics Manuals}
Below are listings of the contents of the ``EC Manual'' for quick reference or ease of acquiring the texts from the library, etc.

%\textbf{Required Texts:}
\begin{itemize}
	\item \textit{Eastern Classic Photocopies -- Fall Readings, Seminar $|$ Preceptorial, 2024-2025 Edition}, (also referred to as the ``EC Manual'') -- collection of selected texts printed by St. John's for the Fall Seminar and both Fall Preceptorials
	      \begin{enumerate}
		      \item ``Seminar Readings''
		            \begin{enumerate}
			            \item TODO: fill out these selections
		            \end{enumerate}
		      \item ``Preceptorial Readings''
		            \begin{enumerate}
			            \item TODO: fill out these selections
		            \end{enumerate}
	      \end{enumerate}
	\item \textit{Eastern Classic Photocopies -- Seminar, 2023}, (also referred to as the ``EC Manual'') -- collection of selected texts printed by St. John's for the Spring Seminar
	      \begin{enumerate}
		      \item Kālidāsa, \emph{Kumārasaṃbhava}, in \emph{The Origin of the Young God}, translated by Hank Hifetz, pp. 3--60 in the EC Manual, pp. 21--131 in original text
		      \item ``The \emph{Dhvanyāloka} of Ānandavardhana with the \emph{Locana} of Abhinavagupta'' selections with supplemental material by Keith and Perry, pp. 61--160 in the EC Manual, various pages selected from original text
		      \item TODO: fill out these selections
	      \end{enumerate}
	\item Kālidāsa, \emph{The Recognition of Śhakuntalā}, translated by W.J. Johnson.
	\item TODO: add other books?
\end{itemize}


\subsection{Seminar Readings}
Individual books for Seminar are listed in order they are encountered in class.

\begin{itemize}
	\item TODO: fill this out?
\end{itemize}

% TODO: Do i need this? any of this? or is specificity of the manual above useful?
\subsection{Preceptorial Readings}
% TODO: make subsubsections instead of items?
\begin{itemize}
	\item Fall Preceptorial 1
	      \fallPreceptOneReadingList%
	\item Fall Preceptorial 1
	      \fallPreceptTwoReadingList%
	\item Summer Preceptorial
	      \summerPreceptReadingList%
\end{itemize}

% TODO: add QR code to some survey/form through which people can easily submit changes/errors/etc?
% TODO: add QR to online HTML version??

\end{document}

"""
