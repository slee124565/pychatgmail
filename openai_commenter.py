from job_application_msg import JobApplicationMsg
import openai
import re


def main(args):
    targets = []
    # check if args.html_file target file exist
    if args.candidate_file:
        if os.path.isfile(os.path.join(args.src_dir, args.candidate_file)):
            targets.append(args.candidate_file)

    # check if no target file exist, process all files under {src_dir} subdirectory
    if not targets:
        for (_, _, filenames) in os.walk(os.path.join('.', args.src_dir)):
            targets = [file for file in filenames if file.endswith('json')]

    if not targets:
        print(f'no {args.src_dir} file exist to process')
        return

    # read criteria prompt from txt file
    with open(args.prompt_file, 'r') as fh:
        job_criteria = fh.read().strip()

    openai.api_key = args.openai_key
    for file in targets:
        # read JobApplicationMsg from json file
        with open(os.path.join(args.src_dir, file), 'r') as fh:
            resume = JobApplicationMsg(**json.load(fh))

        messages = [
            {"role": "user", "content": job_criteria},
            {"role": "user", "content": f"以下是應徵者的履歷：「{resume.work_experience} {resume.skills}」"},
            # {"role": "user", "content": output},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        if response['choices'][0]['message']['content']:
            comment = re.sub(r'\n\s*\n', '\n', response['choices'][0]['message']['content'])
            with open(os.path.join(args.src_dir, args.candidate_file), 'w') as fh:
                resume.comment = comment
                fh.write(json.dumps(resume.__dict__, indent=2, ensure_ascii=False))
            print(f'{resume.msg_id}, {resume.name}, \n{resume.comment}\n')
        else:
            print(f'{resume.msg_id}, {resume.name}, NO COMMENT !!!\n')


if __name__ == "__main__":
    import argparse
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
        default='output'
    )
    args = parser.parse_args()
    main(args)
