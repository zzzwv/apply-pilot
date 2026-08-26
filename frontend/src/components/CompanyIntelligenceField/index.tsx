import { useEffect, useMemo, useRef, useState } from "react";
import { Alert, Button, Checkbox, Input, Space, Tag, Typography } from "antd";

import { confirmCompanyIntelligence, searchCompanyIntelligence } from "../../api/companyIntelligence";
import { createCompany, searchLocalCompanies, type Company } from "../../api/companies";
import type {
  CompanyCandidate,
  CompanyIntelligenceSearchResult,
  EditableCompanyCandidate,
  EditableRecruitmentLink,
  RecruitmentLinkCandidate,
  VerificationStatus,
} from "../../types/companyIntelligence";

type Props = {
  value?: string;
  initialCompany?: Company;
  onChange: (companyId: string | undefined) => void;
  onRecruitmentLinkChange?: (url: string | undefined) => void;
};

const verificationLabels: Record<VerificationStatus, string> = {
  verified: "已验证",
  candidate: "候选",
  unverified: "未知",
  rejected: "无效",
};

function linkValidationLabel(link: RecruitmentLinkCandidate): string {
  if (link.valid_status === "unknown" || link.http_status === 403 || link.http_status === 429 || !link.http_status) {
    return "暂无法验证";
  }
  if (link.valid_status === "invalid" || link.verification_status === "rejected") return "无效";
  if (link.verification_status === "verified" || link.valid_status === "valid") return "已验证";
  return "候选";
}

function toEditableCandidate(candidate: CompanyCandidate): EditableCompanyCandidate {
  return {
    company_name: candidate.company_name,
    short_name: candidate.short_name ?? null,
    industry: candidate.industry ?? null,
    company_nature: candidate.company_nature ?? null,
    company_size: candidate.company_size ?? null,
    official_website: candidate.official_website ?? null,
    description: candidate.description ?? null,
    recruitment_links: candidate.recruitment_links.map(toEditableLink),
    sources: candidate.sources,
  };
}

function sourceDomain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

function toEditableLink(link: RecruitmentLinkCandidate): EditableRecruitmentLink {
  return {
    title: link.title,
    url: link.url,
    channel_type: link.channel_type,
    claimed_official: link.claimed_official,
    source_url: link.source_url,
    evidence: link.evidence,
  };
}

export function CompanyIntelligenceField({
  value,
  initialCompany,
  onChange,
  onRecruitmentLinkChange,
}: Props) {
  const [companyName, setCompanyName] = useState(initialCompany?.full_name ?? "");
  const [localMatches, setLocalMatches] = useState<Company[]>([]);
  const [searchingLocal, setSearchingLocal] = useState(false);
  const [searchingWeb, setSearchingWeb] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [draft, setDraft] = useState<CompanyCandidate>();
  const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
  const [partial, setPartial] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [manualError, setManualError] = useState<string>();
  const [linkedCompany, setLinkedCompany] = useState<Company | undefined>(initialCompany);
  const [linkedExistingCompany, setLinkedExistingCompany] = useState(Boolean(initialCompany));
  const webRequest = useRef<AbortController | undefined>(undefined);

  useEffect(() => {
    if (initialCompany && value === initialCompany.id) {
      setLinkedCompany(initialCompany);
      setLinkedExistingCompany(true);
    }
  }, [initialCompany, value]);

  useEffect(() => () => webRequest.current?.abort(), []);

  useEffect(() => {
    const keyword = companyName.trim();
    if (!keyword) {
      setLocalMatches([]);
      return undefined;
    }
    const timer = window.setTimeout(async () => {
      setSearchingLocal(true);
      try {
        setLocalMatches(await searchLocalCompanies(keyword));
      } catch {
        setLocalMatches([]);
      } finally {
        setSearchingLocal(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [companyName]);

  const orderedLinks = useMemo(
    () => [...(draft?.recruitment_links ?? [])].sort(
      (first, second) => Number(second.claimed_official) - Number(first.claimed_official),
    ),
    [draft],
  );
  const selectedLinks = useMemo(
    () => orderedLinks.filter((link) => selectedUrls.includes(link.url)),
    [orderedLinks, selectedUrls],
  );

  const applySearchResult = (result: CompanyIntelligenceSearchResult) => {
    setPartial(result.partial);
    setWarnings(result.warnings);
    if (!result.company) {
      setDraft(undefined);
      return;
    }
    const candidate = {
      ...result.company,
      recruitment_links: result.company.recruitment_links.length ? result.company.recruitment_links : result.recruitment_links,
      sources: result.company.sources.length ? result.company.sources : result.sources,
    };
    setDraft(candidate);
    setCompanyName(candidate.company_name);
    setSelectedUrls(candidate.recruitment_links.map((link) => link.url));
    onRecruitmentLinkChange?.(
      [...candidate.recruitment_links].sort(
        (first, second) => Number(second.claimed_official) - Number(first.claimed_official),
      )[0]?.url,
    );
  };

  const selectRecruitmentLink = (link: RecruitmentLinkCandidate, checked: boolean) => {
    const nextUrls = checked
      ? [...selectedUrls, link.url]
      : selectedUrls.filter((url) => url !== link.url);
    setSelectedUrls(nextUrls);
    const nextLink = checked
      ? link
      : orderedLinks.find((candidate) => nextUrls.includes(candidate.url));
    onRecruitmentLinkChange?.(nextLink?.url);
  };

  const fetchWebIntelligence = async () => {
    const keyword = companyName.trim();
    if (!keyword) return;
    const controller = new AbortController();
    webRequest.current?.abort();
    webRequest.current = controller;
    setManualError(undefined);
    setSearchingWeb(true);
    try {
      const result = await searchCompanyIntelligence(keyword, false, controller.signal);
      if (controller.signal.aborted || webRequest.current !== controller) return;
      applySearchResult(result);
    } catch {
      if (controller.signal.aborted || webRequest.current !== controller) return;
      setDraft(undefined);
      setPartial(true);
      setWarnings([]);
      setManualError("联网获取失败或请求过于频繁，请手动创建企业。");
    } finally {
      if (webRequest.current === controller) {
        webRequest.current = undefined;
        setSearchingWeb(false);
      }
    }
  };

  const cancelWebIntelligence = () => {
    webRequest.current?.abort();
    webRequest.current = undefined;
    setSearchingWeb(false);
    setDraft(undefined);
    setPartial(true);
    setWarnings(["联网获取已取消，可手动补充企业信息。"]);
  };

  const chooseLocalCompany = (company: Company) => {
    setLinkedCompany(company);
    setLinkedExistingCompany(true);
    setCompanyName(company.full_name);
    setDraft(undefined);
    setManualError(undefined);
    onChange(company.id);
  };

  const changeCompanyName = (nextName: string) => {
    if (nextName !== companyName && (value || linkedCompany)) {
      onChange(undefined);
      setLinkedCompany(undefined);
      setLinkedExistingCompany(false);
      setDraft(undefined);
      setSelectedUrls([]);
      setPartial(false);
      setWarnings([]);
    }
    setCompanyName(nextName);
  };

  const updateDraft = (field: keyof CompanyCandidate, valueToSet: string) => {
    setDraft((current) => current ? { ...current, [field]: valueToSet || null } : current);
  };

  const confirmCandidate = async () => {
    if (!draft) return;
    setConfirming(true);
    setManualError(undefined);
    try {
      const response = await confirmCompanyIntelligence({
        company: toEditableCandidate(draft),
        aliases: draft.short_name && draft.short_name !== draft.company_name ? [draft.short_name] : [],
        selected_recruitment_links: selectedLinks.map(toEditableLink),
      });
      setLinkedCompany(response.company);
      setLinkedExistingCompany(!response.created);
      setCompanyName(response.company.full_name);
      onChange(response.company.id);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } }).response?.status;
      setManualError(status === 409 ? "企业信息与现有企业冲突，请检查名称或别名后重试。" : "确认企业信息失败，请手动创建企业。");
    } finally {
      setConfirming(false);
    }
  };

  const createManualCompany = async () => {
    const name = companyName.trim();
    if (!name) return;
    cancelWebIntelligence();
    setConfirming(true);
    setManualError(undefined);
    try {
      const company = await createCompany(name);
      setLinkedCompany(company);
      setLinkedExistingCompany(false);
      setPartial(false);
      setWarnings([]);
      onChange(company.id);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } }).response?.status;
      setManualError(status === 409 ? "企业已存在，请从本地企业结果中选择。" : "创建企业失败，请稍后重试。");
    } finally {
      setConfirming(false);
    }
  };

  return (
    <section className="company-intelligence-field" aria-label="企业智能信息">
      <label htmlFor="company-intelligence-name">企业名称</label>
      <Space.Compact style={{ display: "flex", marginTop: 4 }}>
        <Input id="company-intelligence-name" value={companyName} onChange={(event) => changeCompanyName(event.target.value)} placeholder="输入企业名称或别名" />
        <Button type="primary" loading={searchingWeb} onClick={fetchWebIntelligence}>联网获取</Button>
        {searchingWeb && <Button onClick={cancelWebIntelligence}>取消联网获取</Button>}
      </Space.Compact>
      {searchingLocal && <Typography.Text type="secondary">正在查询本地企业...</Typography.Text>}
      {localMatches.length > 0 && (
        <Space wrap style={{ marginTop: 8 }}>
          {localMatches.map((company) => <Button key={company.id} size="small" onClick={() => chooseLocalCompany(company)}>{company.full_name}（本地企业）</Button>)}
        </Space>
      )}
      {linkedCompany && <Alert style={{ marginTop: 8 }} type="success" showIcon message={linkedExistingCompany ? `已关联既有企业：${linkedCompany.full_name}` : `已关联企业：${linkedCompany.full_name}`} />}
      {searchingWeb && <Alert style={{ marginTop: 12 }} type="info" showIcon message="正在获取企业公开信息，联网搜索可能需要几十秒..." />}
      {partial && <Alert style={{ marginTop: 12 }} type="warning" showIcon message="部分信息暂未获取，可手动补充" description={warnings.join("；") || undefined} />}
      {manualError && <Alert style={{ marginTop: 12 }} type="error" showIcon message={manualError} />}

      {draft && (
        <section className="company-intelligence-preview" aria-labelledby="company-intelligence-preview-title">
          <div className="company-intelligence-preview__heading">
            <div>
              <Typography.Title id="company-intelligence-preview-title" level={3}>企业信息预览</Typography.Title>
              <Typography.Text type="secondary">联网获取的信息可在确认前编辑。</Typography.Text>
            </div>
            <Tag className="company-intelligence-preview__verification">验证状态：{verificationLabels[draft.verification_status ?? "unverified"]}</Tag>
          </div>
          <Space className="company-intelligence-preview__fields" direction="vertical" style={{ display: "flex" }}>
            <Input aria-label="企业全称" value={draft.company_name} onChange={(event) => updateDraft("company_name", event.target.value)} />
            <Input aria-label="简称" value={draft.short_name ?? ""} placeholder="简称" onChange={(event) => updateDraft("short_name", event.target.value)} />
            <Input aria-label="行业" value={draft.industry ?? ""} placeholder="行业" onChange={(event) => updateDraft("industry", event.target.value)} />
            <Input aria-label="企业性质" value={draft.company_nature ?? ""} placeholder="企业性质" onChange={(event) => updateDraft("company_nature", event.target.value)} />
            <Input aria-label="企业规模" value={draft.company_size ?? ""} placeholder="企业规模" onChange={(event) => updateDraft("company_size", event.target.value)} />
            <Input aria-label="官网" value={draft.official_website ?? ""} placeholder="官网" onChange={(event) => updateDraft("official_website", event.target.value)} />
            <Input.TextArea aria-label="企业描述" value={draft.description ?? ""} placeholder="企业描述" onChange={(event) => updateDraft("description", event.target.value)} />
          </Space>
          <section className="company-intelligence-preview__section" aria-labelledby="company-intelligence-recruitment-title">
            <Typography.Title id="company-intelligence-recruitment-title" level={4}>招聘链接</Typography.Title>
            <Space className="company-intelligence-preview__list" direction="vertical" style={{ display: "flex" }}>
            {orderedLinks.map((link) => (
              <article className="company-intelligence-link" key={link.url}>
                <div className="company-intelligence-link__title">
                  <Checkbox aria-label={`选择${link.title}`} checked={selectedUrls.includes(link.url)} onChange={(event) => selectRecruitmentLink(link, event.target.checked)}>
                    {link.title}
                  </Checkbox>
                  <Tag className={link.claimed_official ? "company-intelligence-link__provenance company-intelligence-link__provenance--official" : "company-intelligence-link__provenance"}>{link.claimed_official ? "官方招聘" : "第三方来源"}</Tag>
                </div>
                <Typography.Text type="secondary">渠道：{link.channel_type} · 验证：{linkValidationLabel(link)}</Typography.Text>
                <a className="company-intelligence-link__url" href={link.url} target="_blank" rel="noreferrer">{link.url}</a>
                {link.source_url && <div className="company-intelligence-link__source"><Typography.Text type="secondary">来源：</Typography.Text><Typography.Text>{sourceDomain(link.source_url)}</Typography.Text> · <a href={link.source_url} target="_blank" rel="noreferrer">{link.source_url}</a></div>}
                {link.evidence && <Typography.Text type="secondary" style={{ display: "block" }}>依据：{link.evidence}</Typography.Text>}
                {link.last_checked_at && <Typography.Text type="secondary" style={{ display: "block" }}>最后检查：{link.last_checked_at}</Typography.Text>}
              </article>
            ))}
            </Space>
          </section>
          <section className="company-intelligence-preview__section" aria-labelledby="company-intelligence-sources-title">
            <Typography.Title id="company-intelligence-sources-title" level={4}>信息来源</Typography.Title>
            <Space className="company-intelligence-preview__list" direction="vertical" style={{ display: "flex" }}>
              {draft.sources.map((source) => <article className="company-intelligence-source" key={source.url}><div><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a><Tag className={source.source_type === "official" ? "company-intelligence-source__type company-intelligence-source__type--official" : "company-intelligence-source__type"}>{source.source_type === "official" ? "官方来源" : "第三方来源"}</Tag></div><Typography.Text type="secondary">{source.source_type} · {sourceDomain(source.url)}</Typography.Text><a className="company-intelligence-link__url" href={source.url} target="_blank" rel="noreferrer">{source.url}</a></article>)}
            </Space>
          </section>
          <Button className="company-intelligence-preview__confirm" type="primary" loading={confirming} onClick={confirmCandidate}>确认企业信息</Button>
        </section>
      )}

      {!draft && <Button style={{ marginTop: 12 }} loading={confirming} onClick={createManualCompany}>创建手动企业</Button>}
    </section>
  );
}
