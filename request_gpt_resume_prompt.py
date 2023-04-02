import sys

from job_application_msg import JobApplicationMsg
from pprint import pprint
import openai
import re
import os
import dotenv

dotenv.load_dotenv()
SOURCE_DIR = os.getenv('SOURCE_DIR', 'output')
OPENAI_KEY = os.getenv('OPENAI_KEY')
OPENAI_GPT_MODEL = os.getenv('OPENAI_GPT_MODEL', 'gpt-3.5-turbo')
OPENAI_API_TEMPERATURE = os.getenv('OPENAI_API_TEMPERATURE', 0.7)
openai.api_key = OPENAI_KEY


def request_gpt_resume_prompt(msg_id, name, criteria, experiences, skills,
                              gpt_model=OPENAI_GPT_MODEL,
                              openai_api_temperature=float(OPENAI_API_TEMPERATURE)):
    if not openai.api_key:
        raise ValueError(f'OPENAI API KEY Invalid')

    messages = [
        {"role": "user", "content": criteria},
        {"role": "user", "content": f"工作經歷如下：\n'{experiences}'\n技能專長如下：\n'{skills}'"},
    ]
    print(f'send {msg_id}, {name} for gtp checking ...')
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=messages,
        temperature=openai_api_temperature,
    )
    comment = response['choices'][0]['message']['content'] if response['choices'][0]['message']['content'] else None
    comment = re.sub(r'\n\s*\n', '\n', comment)
    validation = True if comment.upper().find('PASS') >= 0 else False
    print(f'prompt validation: {validation}\ncomment:\n{comment}')
    return validation, comment


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
        sys.exit(-1)

    # read criteria prompt from txt file
    with open(args.prompt_file, 'r') as fh:
        job_criteria = fh.read().strip()

    summary = []
    for file in targets:
        # read JobApplicationMsg from json file
        with open(os.path.join(args.src_dir, file), 'r') as fh:
            resume = JobApplicationMsg(**json.load(fh))
        validation, comment = request_gpt_resume_prompt(
            msg_id=resume.msg_id,
            name=resume.name,
            criteria=job_criteria,
            experiences=resume.work_experience,
            skills=resume.skills
        )
        resume.inspection = validation
        resume.comment = comment
        with open(os.path.join(args.src_dir, file), 'w') as fh:
            fh.write(json.dumps(resume.__dict__, indent=2, ensure_ascii=False))

        # add resume inspection result into summary
        print(f'{resume.msg_id}, {resume.name}, {resume.inspection} \n{resume.comment}\n')
        summary.append([resume.msg_id, resume.name, resume.inspection])

    pprint(summary)


