from __future__ import print_function

import sys

from job_application_msg import JobApplicationMsg
import dotenv
import bs4
from lxml import etree
import os
import json
import re

dotenv.load_dotenv()
SOURCE_DIR = os.getenv('OUTPUT_DIR', 'output')


def convert_resume_104_html(resume_104_file,
                            source_dir=SOURCE_DIR):
    parsed_file = os.path.join(source_dir, f'{os.path.splitext(resume_104_file)[0]}.json')
    # if os.path.exists(parsed_file):
    #     continue
    # print(f'parse {gmail_html_file}')

    parse_res = {
        'email_id': os.path.splitext(resume_104_file)[0]
    }

    html_file = os.path.join(source_dir, resume_104_file)
    with open(html_file, 'r') as fh:
        soup = bs4.BeautifulSoup(fh.read(), 'html.parser')

    dom = etree.HTML(str(soup))
    job = dom.xpath(
        r'/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a'
    )[0].text
    parse_res['應徵職位'] = job
    name = dom.xpath(r'/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr[2]/td/div[1]/b/a/span')[0].text
    parse_res['姓名'] = name

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
                if segment not in parse_res.keys():
                    parse_res[segment] = ''

                parse_res[segment] += '--------------------\n'
                # get all table row data
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th:
                        th_txt = th.text.strip().replace('\n', '')
                        parse_res[segment] += f'#{th_txt}\n'
                    if td:
                        # print(repr(td.contents))
                        # print(repr([type(content) for content in td.contents]))
                        td_txt = td.text.strip()
                        td_txt = re.sub('\n{2,}', '\n', td_txt)
                        if td_txt:
                            parse_res[segment] += f'{td_txt}\n'
                parse_res[segment] += '--------------------\n'

    candidate = JobApplicationMsg(
        msg_id=parse_res.get('email_id'),
        name=parse_res.get('姓名', ''),
        applied_position=job,
        education=parse_res.get('教育背景', ''),
        work_experience=parse_res.get('工作經歷', ''),
        skills=parse_res.get('技能專長', ''),
        self_introduction=parse_res.get('自傳', ''),
    )
    with open(parsed_file, 'w') as f:
        # f.write(json.dumps(parse_res, ensure_ascii=False, indent=2))
        f.write(json.dumps(candidate.__dict__, ensure_ascii=False, indent=2))
    print(f'parse msg {candidate.msg_id}, {candidate.name}, {candidate.applied_position}, output {parsed_file}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--resume_104_file',
                        help='gmail 104 resume html file under sub-directory source_dir',
                        default=None)
    parser.add_argument('-o', '--source_dir',
                        help='output subdirectory name',
                        default='output')

    args = parser.parse_args()
    targets = []

    # check if resume_104_file target file exist
    if args.resume_104_file:
        if os.path.isfile(os.path.join(args.source_dir, args.resume_104_file)):
            targets.append(args.resume_104_file)

    # check if no target file exist, process all files under {source_dir} subdirectory
    if not targets:
        for (_, _, filenames) in os.walk(os.path.join('.', args.source_dir)):
            targets = filenames

    if not targets:
        print(f'no {args.source_dir} file exist to process')
        sys.exit(-1)

    for filename in targets:
        if not filename.endswith('.html'):
            continue

        convert_resume_104_html(
            resume_104_file=filename,
            source_dir=args.source_dir)
