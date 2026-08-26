import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { init } from "echarts/core";

import { DashboardChart } from ".";

vi.mock("echarts/core", () => ({ init: vi.fn(), use: vi.fn() }));
vi.mock("echarts/charts", () => ({ BarChart: {}, LineChart: {}, PieChart: {} }));
vi.mock("echarts/components", () => ({ GridComponent: {}, LegendComponent: {}, TooltipComponent: {} }));
vi.mock("echarts/renderers", () => ({ CanvasRenderer: {} }));

const setOption = vi.fn();
const resize = vi.fn();
const dispose = vi.fn();
const chart = { setOption, resize, dispose };

beforeEach(() => {
  vi.mocked(init).mockReturnValue(chart as unknown as ReturnType<typeof init>);
  Object.defineProperties(HTMLElement.prototype, {
    clientWidth: { configurable: true, get: () => 480 },
    clientHeight: { configurable: true, get: () => 300 },
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DashboardChart", () => {
  it("uses the shared empty presentation without initializing ECharts", () => {
    render(<DashboardChart ariaLabel="示例图" option={{}} isEmpty />);

    expect(screen.getByRole("heading", { name: "暂无图表数据" })).toBeDefined();
    expect(vi.mocked(init)).not.toHaveBeenCalled();
  });

  it("resizes and disposes an initialized chart", () => {
    const { unmount } = render(<DashboardChart ariaLabel="示例图" option={{ series: [] }} isEmpty={false} />);

    expect(vi.mocked(init)).toHaveBeenCalledTimes(1);
    expect(setOption).toHaveBeenCalledWith({ series: [] });
    window.dispatchEvent(new Event("resize"));
    expect(resize).toHaveBeenCalledTimes(1);

    unmount();
    expect(dispose).toHaveBeenCalledTimes(1);
  });
});
