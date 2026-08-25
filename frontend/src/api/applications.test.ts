import { describe, expect, it } from "vitest";

import * as applications from "./applications";
import type { ApplicationInput, ApplicationUpdate } from "../types/application";

describe("toApplicationUpdate", () => {
  it("removes current_status so normal edits cannot bypass status history", () => {
    const convert = (applications as { toApplicationUpdate?: (payload: ApplicationInput) => ApplicationUpdate }).toApplicationUpdate;
    const payload: ApplicationInput = {
      company_id: "123e4567-e89b-12d3-a456-426614174000",
      job_title: "Backend Engineer",
      application_type: "autumn_fulltime",
      application_date: "2026-08-25",
      channel: "official_campus",
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: "updated",
      current_status: "APPLIED",
    };

    const { current_status: _, ...expected } = payload;
    expect(convert).toBeTypeOf("function");
    expect(convert!(payload)).toEqual(expected);
  });
});
