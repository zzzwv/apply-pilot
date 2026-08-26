import { useEffect, useRef } from "react";
import { init, use, type EChartsType } from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

import emptyDashboard from "../../assets/illustrations/empty-dashboard.svg";
import { EmptyState } from "../EmptyState";

use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

type DashboardChartProps = {
  ariaLabel: string;
  option: Parameters<EChartsType["setOption"]>[0];
  isEmpty: boolean;
};

export function DashboardChart({ ariaLabel, option, isEmpty }: DashboardChartProps) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = container.current;
    if (!element || isEmpty || !element.clientWidth || !element.clientHeight) return;
    const chart = init(element);
    chart.setOption(option);
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [isEmpty, option]);

  if (isEmpty) {
    return <EmptyState
      image={{ src: emptyDashboard, alt: "暂无图表数据" }}
      title="暂无图表数据"
      description="当前筛选条件下暂无可展示的图表数据。"
    />;
  }
  return <div ref={container} aria-label={ariaLabel} style={{ height: 300, width: "100%" }} />;
}
