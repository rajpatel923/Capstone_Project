from pydantic import BaseModel


class FlagCapturedPayload(BaseModel):
    range_challenge_id: str
    title: str
    points: int
    student_member_id: str
