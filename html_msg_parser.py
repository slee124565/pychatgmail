from __future__ import print_function

from pprint import pprint

from bs4 import BeautifulSoup
from lxml import etree
import os
import json


def main(args):
    target = []
    # check if args.html_file target file exist
    if args.html_file:
        if os.path.isfile(os.path.join('html', args.html_file)):
            target.append(os.path.join('html', args.html_file))

    # check if no target file exist, process all files under html sub-directory
    if not target:
        for (_, _, filenames) in os.walk(os.path.join('.', 'html')):
            target = filenames
        # target = [file for (_, _, file) in os.walk(os.path.join('.', 'html'))]

    if not target:
        print(f'no html file exist to process')
        return

    for filename in target:
        if not filename.endswith('.html'):
            continue

        parse_res = {}

        html_file = os.path.join('html', filename)
        with open(html_file, 'r') as fh:
            soup = BeautifulSoup(fh.read(), 'html.parser')

        dom = etree.HTML(str(soup))
        job = dom.xpath(
            r'/html/body/table[2]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td/div[2]/a'
        )[0].text
        parse_res['job'] = job

        tables = soup.find_all("table")
        segment = None
        target_segments = [
            '工作經歷',
            '技能專長',
            '自傳'
        ]

        for table in tables:
            if {'table', 'table--620', 'table-fixed', 'bg-white'} == set(table.get('class', [])):
                tds = table.find_all('td')
                for td in tds:
                    if td.text:
                        segment = td.text
                # print(f'segment: {segment}')
            elif {'table', 'table--620', 'table-resume', 'table-fixed', 'bg-white'} == set(table.get('class', [])):
                if segment in target_segments:
                    if segment not in parse_res.keys():
                        parse_res[segment] = ''

                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        # print(repr(td.text))
                        if th and td:
                            th_txt = th.text.strip().replace('\n', '')
                            td_txt = td.text.strip().replace('\n', '')
                            parse_res[segment] += f'#{th_txt}\n{td_txt}\n'
                            # if 'break-all' in td.get('class', []):
                            #     sub_tds = td.find_all('td')
                            #     for sub_td in sub_tds:
                            #         txt = sub_td.text.strip().replace('\n', '')
                            #         if txt:
                            #             parse_res[segment] += f'{txt}\n'
                                # parse_res[segment] += '\n'.join([sub_td.text.strip() for sub_td in sub_tds])
                            # else:
                            #     parse_res[segment] += f'{td.text.strip()}\n'
                        elif td and td.text:
                            txt = td.text.strip().replace('\n', '')
                            if txt:
                                parse_res[segment] += f'{txt}\n'

        for k, v in parse_res.items():
            # print(repr(k))
            # print(repr(v))
            print(k)
            print(v)
            print('======================')
        name, ext = os.path.splitext(filename)
        parsed_file = os.path.join('html', f'{name}.json')
        with open(parsed_file, 'w') as f:
            f.write(json.dumps(parse_res, ensure_ascii=False))
        # break
        print('+++++++++++++++++++++++++++++++')

        # # Find all rows in the table
        # rows = soup.find_all('tr')
        #
        # # Loop through each row and print its cells
        # lines = []
        # for row in rows:
        #     heads = row.find_all('th')
        #     cells = row.find_all('td')
        #     line = '\t'.join(str(cell.text).strip() for cell in heads+cells).replace('\n', '')
        #     if not line.strip():
        #         continue
        #     # print(line)
        #     lines.append(line)
        #     pass
        #
        # # Save html parser result
        # name, ext = os.path.splitext(filename)
        # txt_file = os.path.join('html', f'{name}.txt')
        # with open(txt_file, 'w') as fh:
        #     fh.write('\n'.join(lines))
        # print(f'convert {filename} to {txt_file}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--html_file',
                        help='html file name under sub-directory ./html',
                        default=None)

    args = parser.parse_args()
    main(args)
