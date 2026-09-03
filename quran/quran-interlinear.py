# #!/usr/bin/env python3

# TODO merge/move into arabic-apis repo

import json
import logging
import os
import re

import requests
from dotenv import load_dotenv
from tqdm import tqdm


# https://api-docs.quran.foundation/docs/content_apis_versioned/4.0.0/content-apis/


def get_access_token(url_base, client_id, client_secret):
    logging.debug(
        "Getting access token for client_id: "
        + client_id
        + " from url: "
        + url_base
        + "/oauth2/token"
    )
    # client_id = 'YOUR_CLIENT_ID'
    # client_secret = 'YOUR_CLIENT_SECRET'

    response = requests.post(
        url_base + "/oauth2/token",
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=client_credentials&scope=content",
    )

    return response.json()["access_token"]


# Get list of recitations
# https://api-docs.quran.foundation/docs/content_apis_versioned/recitations/
def get_recitations(url_base, access_token, client_id):
    response = requests.get(
        url_base + "/content/api/v4/resources/recitations",
        headers={
            "Accept": "application/json",
            "x-auth-token": access_token,
            "x-client-id": client_id,
        },
    )

    return response.json()


# recitations = [{'id': 2, 'reciter_name': 'AbdulBaset AbdulSamad', 'style': 'Murattal', 'sound': 'sloow. fine.',
#                 'translated_name': {'language_name': 'english', 'name': 'AbdulBaset AbdulSamad'}},
#                {'id': 1, 'reciter_name': 'AbdulBaset AbdulSamad', 'style': 'Mujawwad', 'sound': 'sloooow stylized',
#                 'translated_name': {'language_name': 'english', 'name': 'AbdulBaset AbdulSamad'}},
#                {'id': 3, 'reciter_name': 'Abdur-Rahman as-Sudais', 'style': None, 'sound': 'Bad echo',
#                 'translated_name': {'language_name': 'english', 'name': 'Abdur-Rahman as-Sudais'}},
#                {'id': 4, 'reciter_name': 'Abu Bakr al-Shatri', 'style': None, 'sound': 'slight nasal',
#                 'translated_name': {'language_name': 'english', 'name': 'Abu Bakr al-Shatri'}},
#                {'id': 5, 'reciter_name': 'Hani ar-Rifai', 'style': None, 'sound': 'high',
#                 'translated_name': {'language_name': 'english', 'name': 'Hani ar-Rifai'}},
#                {'id': 12, 'reciter_name': 'Mahmoud Khalil Al-Husary', 'style': 'Muallim', 'sound': 'sloooow, clear',
#                 'translated_name': {'language_name': 'english', 'name': 'Mahmoud Khalil Al-Husary'}},
#                {'id': 6, 'reciter_name': 'Mahmoud Khalil Al-Husary', 'style': None, 'sound': 'slow clear',
#                 'translated_name': {'language_name': 'english', 'name': 'Mahmoud Khalil Al-Husary'}},

#                {'id': 7, 'reciter_name': 'Mishari Rashid al-`Afasy', 'style': None, 'sound': 'sometimes fast, pleasant resonance echo',
#                 'translated_name': {'language_name': 'english', 'name': 'Mishari Rashid al-`Afasy'}},

#                {'id': 9, 'reciter_name': 'Mohamed Siddiq al-Minshawi', 'style': 'Murattal', 'sound': 'kids repeat?',
#                 'translated_name': {'language_name': 'english', 'name': 'Mohamed Siddiq al-Minshawi'}},
#                {'id': 8, 'reciter_name': 'Mohamed Siddiq al-Minshawi', 'style': 'Mujawwad', 'sound': 'medium slow good resonance echo sometimes too much',
#                 'translated_name': {'language_name': 'english', 'name': 'Mohamed Siddiq al-Minshawi'}},
#                {'id': 10, 'reciter_name': 'Sa`ud ash-Shuraym', 'style': None, 'sound': 'nasal, neat cadence',
#                 'translated_name': {'language_name': 'english', 'name': 'Sa`ud ash-Shuraym'}},
#                {'id': 11, 'reciter_name': 'Mohamed al-Tablawi', 'style': None, 'sound': 'not on website?',
#                 'translated_name': {'language_name': 'english', 'name': 'Mohamed al-Tablawi'}}]


def get_recitation_filelist(
    url_base, access_token, client_id, recitation_id, chapter_number
):
    # Get list of audio files by recitation id
    # NOTE: this is all files by chapter, there will be probably be more than one page.
    query_page_number = 1
    audio_files_list = []

    url = "https://apis-prelive.quran.foundation/content/api/v4/recitations/:recitation_id/by_chapter/:chapter_number"
    while True:
        response = requests.get(
            url_base
            + "/content/api/v4/recitations/"
            + str(recitation_id)
            + "/by_chapter/"
            + str(chapter_number)
            + "?page="
            + str(query_page_number)
            + "&per_page=50",
            headers={
                "Accept": "application/json",
                "x-auth-token": access_token,
                "x-client-id": client_id,
            },
        )

        #     "audio_files": [
        #         {
        #             "verse_key": "1:1",
        #             "url": "Alafasy/mp3/001001.mp3"
        #         }
        #     ],
        #     "pagination": {
        #         "per_page": 10,
        #         "current_page": 1,
        #         "next_page": null,
        #         "total_pages": 1,
        #         "total_records": 7
        #     }

        # Check if we have reached the end of the page
        if response.json()["pagination"]["total_pages"] == query_page_number:
            audio_files_list.extend(response.json()["audio_files"])
            break
        else:
            query_page_number += 1
            # save audio file list from response
            audio_files_list.extend(response.json()["audio_files"])

    # return response.json()["audio_files"]

    # # Loop though audio files and return list of urls
    # audio_files_list = []
    # # working example: https://verses.quran.foundation/Alafasy/mp3/001005.mp3
    # audio_base_url = "https://verses.quran.foundation/"
    # for audio_file in response.json()["audio_files"]:
    #     # Check that url starts with 'http', if not, add base url
    #     if not audio_file["url"].startswith("http"):
    #         audio_files_list.append(audio_base_url + audio_file["url"])
    #     else:
    #         audio_files_list.append(audio_file["url"])
    #
    return audio_files_list


def get_audio_files_from_json(
    audio_files_list, output_path, chapter_number=None, verse_number=None
):
    # Check that output path exists, if not, create it
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # working example: https://verses.quran.foundation/Alafasy/mp3/001005.mp3
    audio_base_url = "https://verses.quran.foundation/"
    chapter_abbreviation = "ch"
    # chapter_abbreviation = "surah"
    verse_abbreviation = "v"
    # verse_abbreviation = "ayah"

    output_results = {}

    # Loop through json response with audio files and name them nicely, then download them
    for audio_file in audio_files_list:
        audio_verse_number = audio_file["verse_key"].split(":")[1]
        if verse_number is not None:
            if int(audio_verse_number) != verse_number:
                # only process the one verse number passed in
                continue

        # Get Chapter and Verse number from verse key
        audio_verse_number_padded = audio_verse_number.zfill(3)
        audio_chapter_number = audio_file["verse_key"].split(":")[0].zfill(3)
        audio_chapter_number_padded = audio_chapter_number.zfill(3)

        # Check that url starts with 'http', if not, add base url
        if not audio_file["url"].startswith("http"):
            audio_file_url = audio_base_url + audio_file["url"]
        else:
            audio_file_url = audio_file["url"]

        # Get file name from url
        audio_file_reciter_name = audio_file_url.split("/")[-3]
        audio_file_extension = audio_file_url.split("/")[-1].split(".")[-1]

        # Make nice name for audio file
        audio_file_name = (
            audio_file_reciter_name
            + "-"
            + chapter_abbreviation
            + audio_chapter_number_padded
            + "-"
            + verse_abbreviation
            + audio_verse_number_padded
            + "-"
            + audio_file_extension
        )

        # Check if file already exists, if so, skip it
        if os.path.exists(output_path + audio_file_name):
            logging.debug("File already exists, skipping: ".format(audio_file_name))
            output_results.update(
                {
                    "chapter": audio_chapter_number,
                    "verse": audio_verse_number,
                    "file_path": output_path + audio_file_name,
                    "reciter_name": audio_file_reciter_name,
                    "response_code": 100,
                }
            )
            continue

        # Download file
        logging.debug("Downloading: ".format(audio_file_name))
        r = requests.get(audio_file_url, allow_redirects=True)
        open(output_path + audio_file_name, "wb").write(r.content)

        output_results.update(
            {
                "chapter": audio_chapter_number,
                "verse": audio_verse_number,
                "file_path": output_path + audio_file_name,
                "reciter_name": audio_file_reciter_name,
                "response_code": r.status_code,
            }
        )

    return output_results


def download_audio_files(audio_files_list, output_path):
    # Check that output path exists, if not, create it
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Loop through audio files and download them
    for audio_file in audio_files_list:
        # Get file name from url
        audio_file_name = audio_file.split("/")[-3] + "_" + audio_file.split("/")[-1]

        # Check if file already exists, if so, skip it
        if os.path.exists(output_path + audio_file_name):
            print("File already exists, skipping: " + audio_file_name)
            continue

        # Download file
        print("Downloading: " + audio_file_name)
        r = requests.get(audio_file, allow_redirects=True)
        open(output_path + audio_file_name, "wb").write(r.content)


def get_chapter(url_base, access_token, client_id, chapter_number=None):
    if chapter_number:
        logging.debug(
            "Getting chapter {} from url: {}/content/api/v4/chapters".format(
                chapter_number, url_base
            )
        )
    else:
        logging.debug(
            "Getting all chapters from url: {}/content/api/v4/chapters/".format(
                url_base
            )
        )
    if chapter_number:
        url_request = url_base + "/content/api/v4/chapters/" + str(chapter_number)
    else:
        url_request = url_base + "/content/api/v4/chapters/"

    response = requests.get(
        # url_base + "/content/api/v4/chapters/",
        url_request,
        headers={"x-auth-token": access_token, "x-client-id": client_id},
    )

    return response.json()


def get_verse(
    url_base, access_token, client_id, chapter_number, verse_number, translations=None
):
    response = requests.get(
        url_base + "/content/api/v4/verses/by_key/" + f"{chapter_number}:{verse_number}"
        # + f"?fields=text_indopak"
        + f"?fields=text_indopak,text_uthmani,text_imlaei" + f"&translations=19,20",
        headers={
            "Accept": "application/json",
            "x-auth-token": access_token,
            "x-client-id": client_id,
        },
    )

    return response.json()


def get_translations(url_base, access_token, client_id):
    response = requests.get(
        url_base + "/content/api/v4/resources/translations",
        headers={
            "Accept": "application/json",
            "x-auth-token": access_token,
            "x-client-id": client_id,
        },
    )

    return response.json()

    # for x in translations["translations"]:
    #     if x["language_name"] == "english":
    #         print(x)
    #
    # {'id': 85, 'name': 'M.A.S. Abdel Haleem', 'author_name': 'Abdul Haleem', 'slug': 'en-haleem',  'language_name': 'english', 'translated_name': {'name': 'M.A.S. Abdel Haleem', 'language_name': 'english'}}
    # {'id': 84, 'name': 'T. Usmani', 'author_name': 'Mufti Taqi Usmani', 'slug': 'en-taqi-usmani',  'language_name': 'english', 'translated_name': {'name': 'T. Usmani', 'language_name': 'english'}}
    # {'id': 95, 'name': 'A. Maududi (Tafhim commentary)', 'author_name': 'Sayyid Abul Ala Maududi', 'slug': 'en-al-maududi',  'language_name': 'english', 'translated_name': {'name': 'A. Maududi (Tafhim commentary)', 'language_name': 'english'}}
    # {'id': 22, 'name': 'A. Yusuf Ali', 'author_name': 'Abdullah Yusuf Ali', 'slug': 'quran.en.yusufali',  'language_name': 'english', 'translated_name': {'name': 'A. Yusuf Ali', 'language_name': 'english'}}
    # {'id': 203, 'name': 'Al-Hilali & Khan', 'author_name': 'Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan',  'slug': '', 'language_name': 'english', 'translated_name': {'name': 'Al-Hilali & Khan', 'language_name': 'english'}}

    # {'id': 19, 'name': 'M. Pickthall', 'author_name': 'Mohammed Marmaduke William Pickthall', 'slug': 'quran.en.pickthall',  'language_name': 'english', 'translated_name': {'name': 'M. Pickthall', 'language_name': 'english'}}
    # {'id': 20, 'name': 'Saheeh International', 'author_name': 'Saheeh International', 'slug': 'en-sahih-international',  'language_name': 'english', 'translated_name': {'name': 'Saheeh International', 'language_name': 'english'}}
    # {'id': 57, 'name': 'Transliteration', 'author_name': 'Transliteration', 'slug': 'transliteration',  'language_name': 'english', 'translated_name': {'name': 'Transliteration', 'language_name': 'english'}}
    # 19, 20, 57


# Source - https://stackoverflow.com/a/20007730
# Posted by Ben Davis, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-19, License - CC BY-SA 4.0


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


def tex_escape_text(text):
    # convert footnote <sup foot_note=227235>1</sup> to latex format
    # text = re.sub(r"<sup foot_note=(\d+)>(\d+)</sup>", r"^\textsuperscript{\2}\textsubscript{\1}", text)
    # text = re.sub(r"<sup foot_note=(\d+)>(\d+)</sup>", r"^\\textsuperscript{{\\2}}", text)

    # just remove footnotes
    text = re.sub(r"<sup foot_note=(\d+)>(\d+)</sup>", r"", text)
    # remove unicode 200F character
    # text = re.sub(r"\u200F", "", text)

    return text


def tex_cleanup_text(text):
    # saheeh has this ligature after his name, not sure if the () enclosing will be enough to not mess up arabic verse...
    text = re.sub(r"(ﷺ)", r"(\\ar{ﷺ})", text)

    text = tex_escape_text(text)

    return text


def tex_remove_arabic_marks(text):
    # remove high character marks
    # see https://en.wikipedia.org/wiki/Arabic_(Unicode_block)#Unicode_chart
    chars_to_remove = [
        "\\u06D6".encode("utf-8").decode("unicode-escape"),
        "\\u06D7".encode("utf-8").decode("unicode-escape"),
        "\\u06D8".encode("utf-8").decode("unicode-escape"),
        "\\u06D9".encode("utf-8").decode("unicode-escape"),
        "\\u06DA".encode("utf-8").decode("unicode-escape"),
        "\\u06DB".encode("utf-8").decode("unicode-escape"),
        "\\u06DC".encode("utf-8").decode("unicode-escape"),
        "\\u06E0".encode("utf-8").decode("unicode-escape"),
        "\\u06E1".encode("utf-8").decode("unicode-escape"),
        "\\u06E2".encode("utf-8").decode("unicode-escape"),
        "\\u06E3".encode("utf-8").decode("unicode-escape"),
        "\\u06E4".encode("utf-8").decode("unicode-escape"),
        "\\u06E5".encode("utf-8").decode("unicode-escape"),
        "\\u06E6".encode("utf-8").decode("unicode-escape"),
        "\\u06E7".encode("utf-8").decode("unicode-escape"),
        "\\u06E8".encode("utf-8").decode("unicode-escape"),
    ]
    regex_pattern = "[" + re.escape("".join(chars_to_remove)) + "]"
    text = re.sub(regex_pattern, "", text)

    return text


def tex_write_verse(fh, verse, chapter_number, verse_number):
    logging.debug(f"Writing verse {chapter_number}:{verse_number}")

    # write chapter and verse number to latex file
    fh.write(
        "\n\n\\noindent[\\textbf{{{}:{}}}]\n".format(
            chapter_number,
            verse_number,
        )
    )

    # loop through translations
    for translation in verse["verse"]["translations"]:
        # translator's name and then translation

        translations_english = {
            "85": "M.A.S. Abdel Haleem",
            "84": "T. Usmani",
            "95": "A. Maududi (Tafhim commentary)",
            "22": "A. Yusuf Ali",
            "203": "Al-Hilali & Khan",
            "19": "M. Pickthall",
            "20": "Saheeh Intl.",
            "57": "Transliteration",
        }
        # {'id': 19, 'name': 'M. Pickthall', 'author_name': 'Mohammed Marmaduke William Pickthall', 'slug': 'quran.en.pickthall',  'language_name': 'english', 'translated_name': {'name': 'M. Pickthall', 'language_name': 'english'}}
        # {'id': 20, 'name': 'Saheeh International', 'author_name': 'Saheeh International', 'slug': 'en-sahih-international',  'language_name': 'english', 'translated_name': {'name': 'Saheeh International', 'language_name': 'english'}}
        # {'id': 57, 'name': 'Transliteration', 'author_name': 'Transliteration', 'slug': 'transliteration',  'language_name': 'english', 'translated_name': {'name': 'Transliteration', 'language_name': 'english'}}

        verse_translator_name = translations_english[str(translation["resource_id"])]
        fh.write(
            "\\textit{{{}}}: {}\n\n".format(
                verse_translator_name,
                tex_cleanup_text(translation["text"]),
            )
        )

    # write arabic text to the latex file at the end of the translations, so that the chapter:verse number is on the left hand side of this block
    fh.write("{\\Large\n")
    fh.write("\\begin{Arabic}\n")
    fh.write(
        "{}\n".format(
            tex_remove_arabic_marks(verse["verse"]["text_uthmani"]),
        )
    )
    fh.write("\\end{Arabic}\n")
    fh.write("}\n")
    fh.write("\\vspace{0.5ex}\n\n")


def tex_write_header(fh):
    # write the beginning of the latex document
    string_header = r"""\documentclass[a4paper, notitlepage, openany, DIV = 14]{scrbook}
\usepackage[x11names]{xcolor}
\usepackage{hyperref}
\hypersetup{
    colorlinks=true, %set true if you want colored links
    linktoc=all,     %set to all if you want both sections and subsections linked
    linkcolor=Blue4,  %choose some color if you want links to stand out
}

%---------- headers and footers --------------
\usepackage[automark]{scrlayer-scrpage}
\makeatletter
\def\chaptermark#1{%
      \markboth {\protect\hyperlink{\@currentHref}{\MakeUppercase{%
        \ifnum \c@secnumdepth >\m@ne
          \if@mainmatter
            \@chapapp\ \thechapter. \ %
          \fi
        \fi
        #1}}}{}}%
    \def\sectionmark#1{%
      \markright {\protect\hyperlink{\@currentHref}{\MakeUppercase{%
        \ifnum \c@secnumdepth >\z@
          \thesection. \ %
        \fi
        #1}}}} 
\makeatother

\ohead{\leftmark}
\rohead{\rightmark}

\pagestyle{scrheadings}

%-------- header
% \ihead{}            % empty header
% \chead{}            % empty header
% \ohead{}            % empty header
%-------- footer
\ifoot{v1.1}   % inner footer with a fixed text
\cfoot{\hyperlink{toc}{Link back to: Table of Contents}}   % central footer
% \cfoot{\headmark}   % central footer with heading on level 1 (section)
% \ofoot{\pagemark}   % outer footer with the page number

\usepackage{polyglossia}
% Set up languages
\setmainlanguage{english}
\setotherlanguage{arabic}
% Set up fonts
\setmainfont{Charis} % supports all IPA symbols
\newfontfamily\arabicfont[Script=Arabic]{Noto Naskh Arabic}  % For Arabic text
\newfontfamily\arabicfonttt[Script=Arabic]{Noto Kufi Arabic} % For Arabic monospace
\newfontfamily\symbolfont{Symbola} % For emojis/symbols
\newcommand{\ar}[1]{{\textarabic{#1}}}
\newcommand{\arpar}[1]{
\begin{Arabic}{\Large #1}
\end{Arabic}}


% \setcounter{secnumdepth}{0} % sections are level 1
\setcounter{secnumdepth}{-1} % sections are level 1

% yes this is redundant/not used, but keeping
\title{Quran Readings: Pickthall and Saheeh International}
\author{Compiled by Justin Lowe from \href{https://quran.com/developers}{Quran.com's API}}

\begin{document}

% \maketitle
\begin{titlepage}
    \centering
    {\Huge\bfseries Quran Readings: Pickthall and Saheeh International\par}
    \vspace{2cm}
    {\Large Compiled by Justin Lowe from \href{https://quran.com/developers}{Quran.com's API}\par}
    \vfill
    {\large 
        \textbf{Changelog:} 

        v1.0 - 2025-11-19: Initial release
        
        v1.1 - 2025-11-19: Added Arabic text
        \par}
    % {\large \today\par}
\end{titlepage}

\hypertarget{toc}{
\tableofcontents
}
\clearpage

"""

    fh.write(string_header)

    return None


def main():
    download_audio = False
    write_tex_file = True
    split_sessions = False

    output_tex_file_path = "quran-interlinear.tex"
    output_path_audio = "audio_files/"

    # Configure logging
    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Load CLIENT_ID and CLIENT_SECRET from dot env file
    load_dotenv(dotenv_path=".env")

    test_api = False
    if test_api:
        CLIENT_ID = os.getenv("CLIENT_ID_TEST")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET_TEST")
        url_oauth_base = os.getenv("END_POINT_TEST")
        url_api_base = os.getenv("URL_API_TEST")
    else:
        CLIENT_ID = os.getenv("CLIENT_ID_LIVE")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET_LIVE")
        url_oauth_base = os.getenv("END_POINT_LIVE")
        url_api_base = os.getenv("URL_API_LIVE")

    api_token = get_access_token(url_oauth_base, CLIENT_ID, CLIENT_SECRET)

    recitations = get_recitations(url_api_base, api_token, CLIENT_ID)

    # Load Quran Readings from JSON file
    try:
        readings_file = os.getenv("SELECTIONS_FILE")
    except:
        readings_file = "quran_readings.json"

    try:
        with open(readings_file, "r") as f:
            sessions = json.load(f)
        logging.debug("Loaded Quran Readings from {}".format(readings_file))
    except Exception as e:
        logging.critical("Failed to load Quran Readings from {}".format(readings_file))

    # # debug print reading assignments
    # for x in sessions:
    #     if x["readings"]:
    #         print("For Session {}:".format(x["session_number"]))
    #     else:
    #         print("For Session {}: No Quran Readings".format(x["session_number"]))
    #     for y in x["readings"]:
    #         if y["verse"]:
    #             if len(y["verse"]) > 1:
    #                 print(
    #                     "Chapter {}: {} - {}".format(
    #                         y["chapter"], y["verse"][0], y["verse"][1]
    #                     )
    #                 )
    #             else:
    #                 print("Chapter {}: {}".format(y["chapter"], y["verse"][0]))
    #         else:  # 'complete' i.e. read all verses in chapter
    #             print("Chapter {}: complete".format(y["chapter"]))

    if write_tex_file:
        # open output file to write tex to
        output_fh_tex = open(output_tex_file_path, "w")

        tex_write_header(output_fh_tex)

    pbar_sessions = tqdm(sessions, desc="Processing Session", position=0)
    for session in pbar_sessions:
        pbar_sessions.set_description(
            "Processing Session {}".format(str(session["session_number"]))
        )

        if session["readings"]:
            logging.debug(f"Writing session {session['session_number']}")
            if write_tex_file:
                # write session number to latex file as section title
                output_fh_tex.write(
                    "\\chapter{{Session {}}}\n".format(session["session_number"])
                )

            if download_audio:
                # make a subdirectory in output_path for this session
                session_number_padded = str(session["session_number"]).zfill(2)
                session_output_path_audio = (
                    output_path_audio + "session_" + session_number_padded + "/"
                )
                if not os.path.exists(session_output_path_audio):
                    os.makedirs(session_output_path_audio)
        else:
            # There are no readings for this session, skip
            continue

        pbar_readings = tqdm(
            session["readings"], desc="-Processing Reading", position=1, leave=False
        )
        for reading in pbar_readings:
            pbar_readings.set_description(
                "-Processing Chapter {}".format(str(reading["chapter"]))
            )
            # Get chapter info
            # TODO do something with this info always?
            chapter_info = get_chapter(
                url_api_base, api_token, CLIENT_ID, reading["chapter"]
            )

            if download_audio:
                # Get audio files for this chapter by recitation id 7 (Mishari Rashid al-`Afasy)
                audio_filelist = get_recitation_filelist(
                    url_api_base, api_token, CLIENT_ID, 7, reading["chapter"]
                )

            if write_tex_file:
                # write chapter number and arabic name and english name to latex file as subsection title
                output_fh_tex.write(
                    # "\\subsection{{Surah {}, {} (English: {})}}\n".format(
                    "\\section{{Surah {}, {} ({})\n".format(  # NOTE: subsection is not closed!
                        reading["chapter"],
                        chapter_info["chapter"]["name_complex"],
                        chapter_info["chapter"]["translated_name"]["name"],
                    )
                )

            # TODO: create link to local audio file. See: https://en.wikibooks.org/wiki/LaTeX/Hyperlinks#Local_file
            #       Something like: `\href{run:/path/to/my/file.ext}{text displayed}`
            # Make array of verses to process
            verses_to_process = []
            verses_all = False
            if reading["verse"]:
                if len(reading["verse"]) > 1:
                    verses_to_process = range(
                        reading["verse"][0], reading["verse"][1] + 1
                    )
                    if write_tex_file:
                        output_fh_tex.write(
                            "Verses {} -- {}}}\n".format(
                                reading["verse"][0], reading["verse"][1]
                            )  # Closes subsection
                        )
                else:
                    verses_to_process = [reading["verse"][0]]
                    # write verse number to latex file
                    if write_tex_file:
                        output_fh_tex.write(
                            "Verse {}}}\n".format(reading["verse"][0])
                        )  # Closes subsection
            else:  # 'complete' i.e. read all verses in chapter
                verses_to_process = range(
                    1, chapter_info["chapter"]["verses_count"] + 1
                )  # write verse numbers to latex file
                if write_tex_file:
                    output_fh_tex.write(
                        "All Verses ({} -- {})}}\n".format(  # Closes subsection
                            1, chapter_info["chapter"]["verses_count"]
                        )
                    )
                verses_all = True

            if write_tex_file:
                # write revelation order to latex file
                # output_fh_tex.write("\\begin{arabtext}\n")
                # output_fh_tex.write("\\begin{center}\n")
                output_fh_tex.write(
                    "\nThe {} revealed Surah. Revealed in {}\n".format(
                        ordinal(chapter_info["chapter"]["revelation_order"]),
                        chapter_info["chapter"]["revelation_place"].capitalize(),
                    )
                )
                # output_fh_tex.write("\\end{center}\n")
                # output_fh_tex.write("\\end{arabtext}\n")
            pbar_verses = tqdm(
                verses_to_process, desc="--Processing Verse", position=2, leave=False
            )
            for verse_num in pbar_verses:
                pbar_verses.set_description(
                    "--Processing Verse {}".format(str(verse_num))
                )

                if download_audio:
                    # Download verse audio
                    results = get_audio_files_from_json(
                        audio_filelist,
                        session_output_path_audio,
                        reading["chapter"],
                        verse_num,
                    )

                    if results:
                        if results["response_code"] == 200:
                            logging.debug(
                                "Audio file downloaded for Ch {}, V {} saved to {}".format(
                                    results["chapter"],
                                    results["verse"],
                                    results["file_path"],
                                )
                            )
                        elif results["response_code"] == 100:
                            logging.debug(
                                "Audio file already exists for Ch {}, V {} at {} - did NOT download file.".format(
                                    results["chapter"],
                                    results["verse"],
                                    results["file_path"],
                                )
                            )
                        else:
                            logging.error(
                                "Error code {} when downloading audio file for Ch {}, V {}: {}".format(
                                    results["code"],
                                    results["chapter"],
                                    results["verse"],
                                    results["message"],
                                )
                            )
                    else:
                        logging.error(
                            "Error downloading audio file for Ch {}, V {}: Function returned nothing.".format(
                                reading["chapter"], verse_num
                            )
                        )

                # TODO error handling on response
                response_verse = get_verse(
                    url_api_base, api_token, CLIENT_ID, reading["chapter"], verse_num
                )

                if write_tex_file:
                    tex_write_verse(
                        output_fh_tex, response_verse, reading["chapter"], verse_num
                    )

    if write_tex_file:
        # write end of latex document
        output_fh_tex.write("\\end{document}\n")
        output_fh_tex.close()


if __name__ == "__main__":
    main()

# TODO save results of API calls, and after done with all, THEN write tex file.
# TODO allow load of json file (saved from above TODO), as looping through reading assignments, if verse not avail THEN do api call, otherwise use local
# TODO after load json file prompt user for what translations/arabic to write out
