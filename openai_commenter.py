import openai


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


if __name__ == "__main__":
    import argparse
    import csv
    import os
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--openai_key', help='openai api key', required=True)
    args = parser.parse_args()

    # load job conditions
    job_condition = {}
    with open('job_condition.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_condition[row['job title']] = row['condition']
    # print(job_condition)

    # load candidate json files
    to_be_comments = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join('.', 'html')):
        to_be_comments = [os.path.join(dirpath, filename) for filename in filenames if filename.endswith('.json')]
        # print(to_be_comments)

    if not to_be_comments:
        print(f'no new candidate')
        exit()
#
    for to_be_comment in to_be_comments:
        with open(to_be_comment) as jsonFile:
            candidate_info = json.load(jsonFile)

        job_title = candidate_info['應徵職位']

        # set job requirement
        job_requirement = f"""
你是一個專業的{job_title}，我會提供你應徵履歷資料，請判斷該名應徵者是否為合適的{job_title}。
以下為應徵條件:
{job_condition[job_title]}
"""
        # print(job_requirement)

        # compose candidate resume
        resume = f"""
工作經歷：
{candidate_info['工作經歷']}

技能專長:
{candidate_info['技能專長']}
"""
        # print(resume)
#

        comment_output = f"""
請把應徵條件是否符合做成表格，表格欄位要有<應徵條件>｜<符合/不符合/不確定>｜<原因>
若有其他符合優秀的{job_title}條件則另外列點。
若有其他需要顧慮的部分也另外列點。
最後給出總結。
"""

        print(f"comment {candidate_info['email_id']}-{candidate_info['姓名']}")
        judge_bot = OpenaiRecruitJudgeBot(args.openai_key)
        judge_comment = judge_bot.judge_comment(job_requirement, resume, comment_output)
        judge_score = judge_bot.judge_score(job_requirement, resume)

        output_csv = 'openai_comment.csv'
        file_exists = os.path.isfile(output_csv)
        output_dict = {
            'email_id': candidate_info['email_id'],
            'candidate_name': candidate_info['姓名'],
            'candidate_resume': resume,
            'job_requirement': job_condition[job_title],
            'openai_comment': judge_comment,
            'openai_score': judge_score
        }
        with open(output_csv, 'a', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=output_dict.keys(), delimiter=',', lineterminator='\n')
            if not file_exists:
                writer.writeheader()  # file doesn't exist yet, write a header
            writer.writerows([output_dict])

