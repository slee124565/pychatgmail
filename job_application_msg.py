from dataclasses import dataclass


@dataclass
class JobApplicationMsg:
    msg_id: str  # gmail message ID
    name: str  # 應徵者名字
    applied_position: str  # 應徵職務
    education: str  # 教育背景
    work_experience: str  # 工作經驗
    skills: str  # 專長技能
    self_introduction: str  # 自傳
    # msg_receive_date: str  # 應徵快照：2023/03/09 09:34
    # job_104_code: str  # 代碼：1689936700883
    comment: str = ''  # 評論結果

    def __str__(self):
        return f'應徵者: {self.name}\n應徵職務：{self.applied_position}\n評論結果:{self.comment}'
