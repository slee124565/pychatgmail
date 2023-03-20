from __future__ import print_function
from bs4 import BeautifulSoup
import os.path


def main(args):
    html_file = os.path.join('html', args.html_file)
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
    name, ext = os.path.splitext(args.html_file)
    txt_file = os.path.join('html', f'{name}.txt')
    with open(txt_file, 'w') as fh:
        fh.write('\n'.join(lines))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--html_file',
                        help='html file name under sub-directory ./html',
                        default='104_mail_html.sample')

    args = parser.parse_args()
    main(args)
