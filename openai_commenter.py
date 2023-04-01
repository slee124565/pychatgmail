from job_application_msg import JobApplicationMsg
import openai
import re


def main(args):
    # read criteria prompt from txt file
    with open(args.prompt_file, 'r') as fh:
        job_criteria = fh.read().strip()

    # read JobApplicationMsg from json file
    with open(os.path.join(args.src_dir, args.candidate_file), 'r') as fh:
        resume = JobApplicationMsg(**json.load(fh))

    messages = [
        {"role": "user", "content": job_criteria},
        {"role": "user", "content": f"以下是應徵者的履歷：「{resume.work_experience} {resume.skills}」"},
        # {"role": "user", "content": output},
    ]
    # for msg in messages:
    #     print(msg)
    openai.api_key = args.openai_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
    )
    comment = re.sub(r'\n\s*\n', '\n', response['choices'][0]['message']['content'])
    with open(os.path.join(args.src_dir, args.candidate_file), 'w') as fh:
        resume.comment = comment
        fh.write(json.dumps(resume.__dict__, indent=2, ensure_ascii=False))
    print(f'{resume.msg_id}, {resume.name}, \n{resume.comment}\n')


if __name__ == "__main__":
    import argparse
    # import csv
    import os
    import json
    import dotenv

    dotenv.load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-k', '--openai_key',
        help='openai api key',
        default=os.getenv('OPENAI_KEY'))
    parser.add_argument(
        '-p', '--prompt_file',
        help='openai prompt text content',
        default=os.getenv('PROMPT_FILE', None)
    )
    parser.add_argument(
        '-f', '--candidate_file',
        help='candidate parsed data file',
        default=os.getenv('CANDIDATE_FILE', None)
    )
    parser.add_argument(
        '--src_dir',
        help='candidate json src subdirectory',
        default='html'
    )
    args = parser.parse_args()
    main(args)
