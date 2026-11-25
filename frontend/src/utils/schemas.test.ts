import { describe, expect, it } from "vitest";
import { pct, titleCase } from "./format";
import { cropSchema, fertilizerSchema, registerSchema, forgotPasswordSchema, resetPasswordSchema } from "./schemas";

describe("schemas", () => {
  it("rejects weak passwords", () => {
    const base = { full_name: "Ali Khan", email: "ali@example.com", account_type: "farmer" as const };
    expect(registerSchema.safeParse({ ...base, password: "short1" }).success).toBe(false);
    expect(registerSchema.safeParse({ ...base, password: "onlyletterslong" }).success).toBe(false);
    expect(registerSchema.safeParse({ ...base, password: "Str0ngPassw0rd" }).success).toBe(true);
  });
  it("enforces crop input bounds", () => {
    const ok = { nitrogen: 80, phosphorus: 50, potassium: 40, temperature: 20, humidity: 60, ph: 7, rainfall: 100 };
    expect(cropSchema.safeParse(ok).success).toBe(true);
    expect(cropSchema.safeParse({ ...ok, ph: 14 }).success).toBe(false);
    expect(cropSchema.safeParse({ ...ok, humidity: "" }).success).toBe(false);
  });
  it("accepts only supported fertilizer growth stages", () => {
    const stages = ["sowing", "vegetative", "flowering", "fruiting", "maturity", "harvest"];
    for (const growth_stage of stages) {
      expect(fertilizerSchema.safeParse({ crop_name: "wheat", growth_stage }).success).toBe(true);
    }
    expect(fertilizerSchema.safeParse({ crop_name: "wheat", growth_stage: "tillering" }).success).toBe(false);
  });
  it("treats blank optional soil values as missing", () => {
    const r = fertilizerSchema.safeParse({ crop_name: "wheat", nitrogen: "", phosphorus: "12", potassium: "", ph: "" });
    expect(r.success).toBe(true);
    if (r.success) { expect(r.data.nitrogen).toBeUndefined(); expect(r.data.phosphorus).toBe(12); }
  });
});

describe("format", () => {
  it("formats", () => { expect(pct(0.923)).toBe("92%"); expect(titleCase("late_blight")).toBe("Late Blight"); });
});

describe("password recovery schemas", () => {
  it("validates forgot-password email addresses", () => {
    expect(forgotPasswordSchema.safeParse({ email: "user@example.com" }).success).toBe(true);
    expect(forgotPasswordSchema.safeParse({ email: "invalid-email" }).success).toBe(false);
  });

  it("accepts valid matching reset passwords", () => {
    const password = "StrongPass123";
    expect(resetPasswordSchema.safeParse({
      new_password: password,
      confirm_password: password,
    }).success).toBe(true);
  });

  it("rejects weak or oversized reset passwords", () => {
    for (const password of ["short1", "onlyletterslong", "1234567890", "A".repeat(129) + "1"]) {
      expect(resetPasswordSchema.safeParse({
        new_password: password,
        confirm_password: password,
      }).success).toBe(false);
    }
  });

  it("rejects mismatched password confirmation", () => {
    expect(resetPasswordSchema.safeParse({
      new_password: "StrongPass123",
      confirm_password: "DifferentPass123",
    }).success).toBe(false);
  });
});
