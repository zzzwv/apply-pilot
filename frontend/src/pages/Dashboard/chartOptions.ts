import type { EChartsType } from "echarts/core";

import { statusColors } from "../../components/StatusTag";
import { statusLabels, type ApplicationStatus } from "../../types/application";
import type {
  CompanyNatureDistributionItem,
  IndustryDistributionItem,
  StatusDistributionItem,
  TrendPoint,
} from "../../types/dashboard";

type ChartOption = Parameters<EChartsType["setOption"]>[0];

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

const tooltip = (params: { name: string; value: number; data: { percentage?: number } }) =>
  `${params.name}<br/>数量：${params.value}<br/>占比：${percent(params.data.percentage ?? 0)}`;

export function statusDistributionOption(items: StatusDistributionItem[]): ChartOption {
  return {
    tooltip: { trigger: "item", formatter: tooltip },
    legend: { bottom: 0 },
    series: [{
      type: "pie",
      radius: "65%",
      data: items.map((item) => ({
        name: statusLabels[item.status],
        value: item.count,
        percentage: item.percentage,
        itemStyle: { color: statusColors[item.status] },
      })),
    }],
  };
}

export function industryDistributionOption(items: IndustryDistributionItem[]): ChartOption {
  return {
    grid: { left: 48, right: 24, top: 28, bottom: 72 },
    tooltip: { trigger: "axis", formatter: (params: Array<{ name: string; value: number; data: { percentage: number } }>) => tooltip(params[0]) },
    xAxis: { type: "category", data: items.map((item) => item.industry), axisLabel: { rotate: 28 } },
    yAxis: { type: "value", minInterval: 1 },
    series: [{ type: "bar", data: items.map((item) => ({ value: item.count, percentage: item.percentage })), itemStyle: { color: "#1677ff" } }],
  };
}

export function companyNatureOption(items: CompanyNatureDistributionItem[]): ChartOption {
  return {
    tooltip: { trigger: "item", formatter: tooltip },
    legend: { bottom: 0 },
    series: [{
      type: "pie",
      radius: "65%",
      data: items.map((item) => ({ name: item.company_nature === "UNKNOWN" ? "未分类" : item.company_nature, value: item.count, percentage: item.percentage })),
    }],
  };
}

export function trendOption(items: TrendPoint[]): ChartOption {
  return {
    grid: { left: 48, right: 24, top: 28, bottom: 48 },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", boundaryGap: false, data: items.map((item) => item.date) },
    yAxis: { type: "value", minInterval: 1 },
    series: [{ type: "line", smooth: true, data: items.map((item) => item.count), areaStyle: { opacity: 0.08 }, itemStyle: { color: "#1677ff" } }],
  };
}
