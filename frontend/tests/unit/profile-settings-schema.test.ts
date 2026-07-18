import { describe, expect, it } from "vitest";

import { profileSettingsSchema } from "@/features/settings/schemas";

describe("profile settings schema", () => {
  const valid = {
    display_name: "Dev Operator",
    username: "dev_operator",
    timezone: "UTC",
    job_title: "SRE",
    avatar_url: "https://example.com/avatar.png",
  };

  it("accepts backend-compatible profile updates", () => {
    expect(profileSettingsSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects invalid usernames and non-HTTPS avatars", () => {
    expect(profileSettingsSchema.safeParse({ ...valid, username: "bad name" }).success).toBe(false);
    expect(profileSettingsSchema.safeParse({ ...valid, avatar_url: "http://example.com/a.png" }).success).toBe(false);
  });
});
