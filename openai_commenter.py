from job_application_msg import JobApplicationMsg
import openai
import json


class OpenaiRecruitJudgeBot:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key

    @staticmethod
    def judge_comment(requirement: str, candidate_resume: str, output: str):
        messages = [
            {"role": "user", "content": requirement},
            {"role": "user", "content": f"以下是應徵者的履歷：「{candidate_resume}」"},
            {"role": "user", "content": output},
        ]
        # for msg in messages:
        #     print(msg)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        res_content = response['choices'][0]['message']['content']
        return res_content

    @staticmethod
    def judge_score(requirement: str, candidate_resume: str) -> float:
        output = """
依照應徵者符合應徵條件，給出一個1~100的分數。只要給數字就好，不要任何文字。
"""
        messages = [
            {"role": "user", "content": requirement},
            {"role": "user", "content": f"以下是應徵者的履歷：「{candidate_resume}」"},
            {"role": "user", "content": output},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        res_content = response['choices'][0]['message']['content']
        return float(res_content)


def main(args):
    targets = []

    # check if args.candidate_file target file exist
    if args.candidate_file:
        if os.path.isfile(os.path.join(args.src_dir, args.candidate_file)):
            targets.append(args.candidate_file)

    # check if no target file exist, process all files under html subdirectory
    if not targets:
        for (_, _, filenames) in os.walk(os.path.join('.', args.src_dir)):
            targets = [file for file in filenames if file.endswith('.json')]
        # target = [file for (_, _, file) in os.walk(os.path.join('.', 'html'))]

    if not targets:
        print(f'no html file exist to process')
        return
    else:
        print(f'targets : {targets}')
        pass

    with open(args.prompt_file, 'r') as fh:
        ai_prompt = fh.read().strip()

    if not ai_prompt:
        print(f'OpenAI prompt error: {ai_prompt}')
        return

    for to_be_comment_file in targets:
        with open(os.path.join(args.src_dir, to_be_comment_file), 'r') as fh:
            data = json.load(fh)
        candidate = JobApplicationMsg(**data)
        ai_prompt = f'{ai_prompt}\n{candidate.work_experience}\n{candidate.skills}'

        # judge_bot = OpenaiRecruitJudgeBot(args.openai_key)
        # judge_comment = judge_bot.judge_comment(job_requirement, resume, comment_output)
        # judge_score = judge_bot.judge_score(job_requirement, resume)


if __name__ == "__main__":
    import argparse
    import csv
    import os
    import json
    import dotenv

    dotenv.load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-k', '--openai_key',
        help='openai api key',
        # required=True,
        default=os.getenv('OPENAI_KEY', None)
    )
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
