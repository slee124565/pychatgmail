import openai


class OpenaiRecruitJudgeBot:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key

    @staticmethod
    def judge(requirement: str, candidate_resume: str, output: str):
        messages = [
            {"role": "user", "content": requirement},
            {"role": "user", "content": f"以下是應徵者的履歷：「{candidate_resume}」"},
            {"role": "user", "content": output},
        ]
        for msg in messages:
            print(msg)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
        )
        res_content = response['choices'][0]['message']['content']
        return res_content
