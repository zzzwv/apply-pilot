from enum import Enum


class ApplicationStatus(str, Enum):
    NOT_APPLIED = "NOT_APPLIED"
    APPLIED = "APPLIED"
    RESUME_PASSED = "RESUME_PASSED"
    FIRST_INTERVIEW = "FIRST_INTERVIEW"
    SECOND_INTERVIEW = "SECOND_INTERVIEW"
    FINAL_INTERVIEW = "FINAL_INTERVIEW"
    HR_INTERVIEW = "HR_INTERVIEW"
    SALARY_NEGOTIATION = "SALARY_NEGOTIATION"
    OFFER_RECEIVED = "OFFER_RECEIVED"
    OFFER_REJECTED = "OFFER_REJECTED"
    RESUME_REJECTED = "RESUME_REJECTED"
    INTERVIEW_REJECTED = "INTERVIEW_REJECTED"
    PROCESS_TERMINATED = "PROCESS_TERMINATED"
    SIGNED = "SIGNED"


class ApplicationType(str, Enum):
    AUTUMN_FULLTIME = "autumn_fulltime"
    SPRING_FULLTIME = "spring_fulltime"
    SUMMER_INTERNSHIP = "summer_internship"
    DAILY_INTERNSHIP = "daily_internship"


class RecruitmentChannel(str, Enum):
    OFFICIAL_CAMPUS = "official_campus"
    OFFICIAL_INTERNSHIP = "official_internship"
    OFFICIAL_SOCIAL = "official_social"
    OFFICIAL_WECHAT = "official_wechat"
    BOSS = "boss"
    ZHILIAN = "zhilian"
    JOB51 = "51job"
    NOWCODER = "nowcoder"
    SHIXISENG = "shixiseng"
    SCHOOL = "school"
    OTHER = "other"


class RecruitmentLinkType(str, Enum):
    OFFICIAL = "official"
    THIRD_PARTY = "third_party"
    CUSTOM = "custom"


class LinkStatus(str, Enum):
    VALID = "valid"
    POSSIBLY_INVALID = "possibly_invalid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
