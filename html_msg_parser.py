from __future__ import print_function

from pprint import pprint

from bs4 import BeautifulSoup
import os


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

    # convert html tr elements into text line data and save result as txt file
    for filename in target:
        html_file = os.path.join('html', filename)
        with open(html_file, 'r') as fh:
            soup = BeautifulSoup(fh.read(), 'html.parser')

        # Find all rows in the table
        rows = soup.find_all('tr')

        # Loop through each row and print its cells
        lines = []
        for row in rows:
            heads = row.find_all('th')
            cells = row.find_all('td')
            line = '\t'.join(str(cell.text).strip() for cell in heads+cells).replace('\n', '')
            if not line.strip():
                continue
            # print(line)
            lines.append(line)
            pass

        # Save html parser result
        name, ext = os.path.splitext(filename)
        txt_file = os.path.join('html', f'{name}.txt')
        with open(txt_file, 'w') as fh:
            fh.write('\n'.join(lines))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--html_file',
                        help='html file name under sub-directory ./html',
                        default=None)

    args = parser.parse_args()
    main(args)
