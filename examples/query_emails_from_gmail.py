# sample code to query emails with filter conditions and save the results to csv file

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/src')

from agmail import GmailApi
import argparse
import csv


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--client_secret', help='GCP service account client-secret json file path', required=True)
    parser.add_argument('-o', '--output_csv', help='the csv file path to store email content', required=True)
    args = parser.parse_args()

    gmail = GmailApi(client_secret_file=args.client_secret)
    all_labels = gmail.query_labels()
    print(f'gmail labels: {all_labels}')

    with open(args.output_csv, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=['date', 'subject', 'ori_message'])
        writer.writeheader()

        next_token = None
        while True:
            emails, next_token = gmail.query_emails(
                labels=['INBOX', 'UNREAD'], query='after:2023/3/16', next_token=next_token)
            writer.writerows(emails)

            if not next_token:
                break
