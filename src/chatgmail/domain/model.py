from dataclasses import dataclass


@dataclass
class Candidate:
    msg_id: str  # gmail message ID
    applied_position: str  # 應徵職務
    self_recommendation: str  # 自我推薦
    msg_receive_date: str  # 應徵快照：2023/03/09 09:34
    job_104_code: str  # 代碼：1689936700883
    name: str  # 應徵者名字
    age: str  # 年齡
    gender: str  # 性別
    work_experiences: object  # 工作經驗
    education: str  # 教育背景
    # skills: str  # 專長技能
    autobiography: str  # 自傳
    comment: str = ''  # 評論結果
    inspection: str = None

    def validate(self) -> bool:
        """
        Validate the candidate data.
        """
        return all(
            [
                self.msg_id,
                self.applied_position,
                self.self_recommendation,
                self.msg_receive_date,
                self.job_104_code,
                self.name,
                self.age,
                self.gender,
                self.work_experiences,
                self.education,
            ]
        )
