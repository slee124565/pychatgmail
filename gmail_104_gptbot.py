from __future__ import print_function

# from convert_resume_104_html import convert_resume_104_html
# from read_gmail_for_subject import read_gmail_for_subject, set_gmail_msg_read
# from request_gpt_resume_prompt import request_gpt_resume_prompt
import openai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import bs4
import re
from lxml import etree
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import dotenv
import base64
import os.path
import os
import logging

dotenv.load_dotenv()
GMAIL_QUERY_DAYS = os.getenv('GMAIL_QUERY_DAYS', -21)
GMAIL_QUERY_SUBJECT_TXT = os.getenv('GMAIL_QUERY_SUBJECT_TXT')
GMAIL_QUERY_LABELS = os.getenv('GMAIL_QUERY_LABELS', 'INBOX')
GMAIL_MSG_MAX = os.getenv('GMAIL_MSG_MAX', 100)
OAUTH_CLIENT_SECRET_FILE = os.getenv('OAUTH_CLIENT_SECRET_FILE', 'credentials.json')
USER_TOKEN_FILE = os.getenv('USER_TOKEN_FILE', 'token.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

OPENAI_KEY = os.getenv('OPENAI_KEY')
OPENAI_GPT_MODEL = os.getenv('OPENAI_GPT_MODEL', 'gpt-3.5-turbo')
OPENAI_GPT_TEMPERATURE = float(os.getenv('OPENAI_GPT_TEMPERATURE', 0.7))
OPENAI_GPT_MAX_TOKEN_LEN = int(os.getenv('OPENAI_GPT_MAX_TOKEN_LEN', 4096))
# PROMPT_CRITERIA_FILE = os.getenv('PROMPT_CRITERIA_FILE', '')
openai.api_key = OPENAI_KEY

OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


@dataclass
class ResumeMsg:
    msg_id: str  # gmail message ID
    name: str  # 應徵者名字
    applied_position: str  # 應徵職務
    education: str  # 教育背景
    experiences: str  # 工作經驗
    skills: str  # 專長技能
    self_introduction: str  # 自傳
    # msg_receive_date: str  # 應徵快照：2023/03/09 09:34
    # job_104_code: str  # 代碼：1689936700883
    gpt_comment: str = ''  # 評論結果
    qualified: str = None  # PASS|FAIL

    def __str__(self):
        return f'應徵者: {self.name}, 應徵職務：{self.applied_position},評論結果:{self.qualified}'


def _convert_104_resume_html(msg_104_body) -> ResumeMsg:
    _convert = {
        'msg_id': None
    }

    soup = bs4.BeautifulSoup(msg_104_body, 'html.parser')
    dom = etree.HTML(str(soup))
    job = dom.xpath(
        r'/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a'
    )[0].text
    _convert['應徵職位'] = job
    name = dom.xpath(r'/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span')[0].text
    _convert['姓名'] = name

    tables = soup.find_all("table")
    segment = None
    target_segments = [
        '工作經歷',
        '技能專長',
        '自傳'
    ]

    for table in tables:
        # segment of resume start
        if {'table', 'table--620', 'table-fixed', 'bg-white'} == set(table.get('class', [])):
            tds = table.find_all('td')
            for td in tds:
                if td.text:
                    segment = td.text
            # print(f'segment: {segment}')
        # segment content
        elif {'table', 'table--620', 'table-resume', 'table-fixed', 'bg-white'} == set(table.get('class', [])):
            if segment in target_segments:
                if segment not in _convert.keys():
                    _convert[segment] = ''

                _convert[segment] += '--------------------\n'
                # get all table row data
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th:
                        th_txt = th.text.strip().replace('\n', '')
                        _convert[segment] += f'#{th_txt}\n'
                    if td:
                        # print(repr(td.contents))
                        # print(repr([type(content) for content in td.contents]))
                        td_txt = td.text.strip()
                        td_txt = re.sub('\n{2,}', '\n', td_txt)
                        if td_txt:
                            _convert[segment] += f'{td_txt}\n'
                _convert[segment] += '--------------------\n'

    _resume = ResumeMsg(
        msg_id=_convert.get('email_id'),
        name=_convert.get('姓名', ''),
        applied_position=job,
        education=_convert.get('教育背景', ''),
        experiences=_convert.get('工作經歷', ''),
        skills=_convert.get('技能專長', ''),
        self_introduction=_convert.get('自傳', ''),
    )
    return _resume


def gmail_104_gpt_hr(title, date_since, qualifications):
    """Process flow
    1. read gmail from inbox with subject matching specific txt and date since Y-m-d
    2. parsing gmail msg content and convert to candidate resume
    3. read job application hr criteria and create gpt prompt with candidate resume
    4. request gpt with candidate resume prompt validation
    5. set gmail msg as unread if candidate resume qualified, otherwise set msg as read
    """
    q_subject = f'104應徵履歷【{title}'

    # Auth gmail with user token
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(USER_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(USER_TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(USER_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        # query user gmail messages
        q_date_since = datetime.strptime(date_since, '%Y-%m-%d').date() if date_since else \
            (date.today() + timedelta(days=int(GMAIL_QUERY_DAYS)))
        service = build('gmail', 'v1', credentials=creds)
        query = f'after:{q_date_since.strftime("%Y/%m/%d")}'
        if q_subject.strip():
            query = f'subject:({q_subject}) {query}'
        logger.info(f'gmail {GMAIL_QUERY_LABELS} query w/ [{query}]')

        results = service.users().messages().list(
            userId='me',
            maxResults=GMAIL_MSG_MAX,
            labelIds=GMAIL_QUERY_LABELS.split(','),
            q=query
        ).execute()
        messages = results.get('messages')
        if not len(messages):
            logger.warning(f'no gmail msg for q {query}')
            return
        logger.info(f'matched messages count: {len(messages)}')

        if not messages:
            logger.warning(f'no gmail message query matched')
            return

        # for each subject matched message
        resumes = []
        for _msg in messages:
            # read gmail msg details from gmail api
            msg_id = _msg.get('id')
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            _msg_subject = next((header['value'] for header in message.get('payload').get('headers') if
                                 header['name'] == 'Subject'), None)
            logger.debug(f'get msg {msg_id} with subject {_msg_subject}')
            if not str(_msg_subject).startswith(q_subject):
                logger.debug(f'skip message subject not started with "{q_subject}", {msg_id}, {_msg_subject}')
                continue

            msg_body_data = message.get('payload').get('body').get('data')
            if not msg_body_data:
                msg_body_data = message.get('payload').get('parts')[0].get('parts')[0].get('body').get('data')
            if not msg_body_data:
                logger.info(f'skip message with no body data, {msg_id}, {_msg_subject}')
                continue
            msg_body = base64.urlsafe_b64decode(msg_body_data).decode("utf-8")
            # convert 104 resume html msg
            resume = _convert_104_resume_html(msg_body)
            resume.msg_id = msg_id
            resumes.append(resume)

            # get job application candidate criteria
            gpt_messages = [
                {"role": "user", "content": qualifications},
                {"role": "user", "content": f"工作經歷如下：\n'{resume.experiences}'\n技能專長如下：\n'{resume.skills}'"},
            ]

            # todo: check _messages token length

            # request gpt w/ resume prompt
            try:
                response = openai.ChatCompletion.create(
                    model=OPENAI_GPT_MODEL,
                    messages=gpt_messages,
                    temperature=float(OPENAI_GPT_TEMPERATURE),
                )
            except openai.error.APIError as err_api:
                logger.error(f'OpenAI API Err: msg {msg_id} {_msg_subject} {err_api}')
                continue

            _comment = response['choices'][0]['message']['content'] \
                if response['choices'][0]['message']['content'] else None
            resume.gpt_comment = re.sub(r'\n\s*\n', '\n', _comment)
            resume.qualified = 'PASS' if _comment.upper().find('PASS') >= 0 else 'FAIL'
            if resume.qualified == 'PASS':
                logger.warning(f'gptBot: {resume}')
                logger.warning(f'{resume.gpt_comment}')
            else:
                logger.info(f'gptBot: {resume}')

            # modify gmail msg read if not qualified
            labels = message['labelIds']
            if 'UNREAD' in labels:
                labels.remove('UNREAD')
                body = {'removeLabelIds': ['UNREAD']}
                service.users().messages().modify(userId='me', id=msg_id, body=body).execute()
                logger.info(f'set gmail msg {msg_id} as read')
            else:
                logger.debug(f'gmail msg {msg_id} already marked as read, skip')

            # save msg_body file with msg_id as filename if OUTPUT_DIR
            if os.path.isdir(OUTPUT_DIR):
                msg_body_data = base64.urlsafe_b64decode(msg_body_data).decode("utf-8")
                output_file = os.path.join(OUTPUT_DIR, f'{msg_id}.html'.replace('/', '_'))
                with open(output_file, 'w') as fh:
                    fh.write(msg_body_data)
                output_json = os.path.splitext(output_file)[0] + ".json"
                with open(output_json, 'w') as fh:
                    json.dump(resume.__dict__, fh, indent=2, ensure_ascii=False)
                logger.debug(f'save msg {[msg_id, _msg_subject, output_file, output_json]}')

        # print resumes report
        logger.warning(f'gptBot get gmail messages count {len(messages)}')

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        logger.error(f'An error occurred: {error}')

    pass


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--q_subject',
                        help='gmail query subject match string',
                        default='UI/UX')
    parser.add_argument('-c', '--criteria_file',
                        help='job criteria prompt file',
                        default='uiux_prompt.txt')
    parser.add_argument('-d', '--q_date_since',
                        help='gmail query date since',
                        default='2023-03-23')
    parser.add_argument('--debug',
                        action='store_true',
                        help='logging level DEBUG',
                        default=False)
    parser.add_argument('--info',
                        action='store_true',
                        help='logging level INFO',
                        default=False)
    # parser.add_argument('-l', '--query_labels',
    #                     help='gmail query labels',
    #                     default=GMAIL_QUERY_LABELS)
    # parser.add_argument('--max_result',
    #                     type=int,
    #                     help='gmail message max number list',
    #                     default=GMAIL_MSG_MAX)
    # parser.add_argument('--oauth_client_secret_file',
    #                     help='gcp project oauth client desktop app credentials file',
    #                     default=OAUTH_CLIENT_SECRET_FILE)
    # parser.add_argument('--user_token_file',
    #                     help='user access and refresh tokens file',
    #                     default=USER_TOKEN_FILE)
    # parser.add_argument('-o', '--output_dir',
    #                     help='output subdirectory name',
    #                     default=OUTPUT_DIR)
    # parser.add_argument('--openai_gpt_model',
    #                     help='openai gpt model name',
    #                     default=OPENAI_GPT_MODEL)
    # parser.add_argument('--openai_key',
    #                     help='openai api key',
    #                     default=OPENAI_KEY)
    # parser.add_argument('--openai_gpt_temperature',
    #                     type=float,
    #                     help='openai gpt temperature arg',
    #                     default=OPENAI_GPT_TEMPERATURE)

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    logger.debug(f'args {args}')
    with open(args.criteria_file) as fp:
        criteria = fp.read().strip()
    gmail_104_gpt_hr(title=args.q_subject, date_since=args.q_date_since, qualifications=criteria)
