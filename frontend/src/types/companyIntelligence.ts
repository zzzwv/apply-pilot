export type Company = {
  id: string;
  full_name: string;
};

export type VerificationStatus = "unverified" | "candidate" | "verified" | "rejected";
export type LinkStatus = "valid" | "possibly_invalid" | "invalid" | "unknown";

export type RecruitmentLinkCandidate = {
  title: string;
  url: string;
  channel_type: string;
  claimed_official: boolean;
  source_url?: string | null;
  evidence?: string | null;
  confidence?: number;
  verification_status?: VerificationStatus;
  valid_status?: LinkStatus;
  http_status?: number | null;
  final_url?: string | null;
};

export type CandidateSource = {
  url: string;
  title: string;
  source_type: string;
  provider?: string | null;
  retrieved_at: string;
};

export type CompanyCandidate = {
  company_name: string;
  short_name?: string | null;
  industry?: string | null;
  company_nature?: string | null;
  company_size?: string | null;
  official_website?: string | null;
  description?: string | null;
  recruitment_links: RecruitmentLinkCandidate[];
  sources: CandidateSource[];
  verification_status?: VerificationStatus;
};

export type CompanyIntelligenceSearchResult = {
  company: CompanyCandidate | null;
  recruitment_links: RecruitmentLinkCandidate[];
  sources: CandidateSource[];
  partial: boolean;
  warnings: string[];
  allow_manual_input: boolean;
};

export type EditableCompanyCandidate = Omit<CompanyCandidate, "verification_status">;
export type EditableRecruitmentLink = Pick<
  RecruitmentLinkCandidate,
  "title" | "url" | "channel_type" | "claimed_official" | "source_url" | "evidence"
>;

export type CompanyIntelligenceConfirmRequest = {
  company: EditableCompanyCandidate;
  aliases: string[];
  selected_recruitment_links: EditableRecruitmentLink[];
};

export type CompanyIntelligenceConfirmResponse = {
  company: Company;
  created: boolean;
  aliases: string[];
  recruitment_links: Array<{
    url: string;
    title: string;
    channel_type: string;
    claimed_official: boolean;
  }>;
};
