import { z } from "zod";

// Empty inputs arrive as "" — treat them as undefined (optional: skipped, required: error).
const blankToUndef = (v: unknown) => (v === "" || v === null || (typeof v === "number" && Number.isNaN(v)) ? undefined : v);
// Required numbers: a blank input must be an error, never silently coerced to 0.
const reqNum = (min: number, max: number, label: string) =>
  z.preprocess(blankToUndef, z.coerce.number({ error: `${label} is required` })
    .min(min, `${label} must be at least ${min}`).max(max, `${label} must be at most ${max}`));

const optNum = (min: number, max: number) =>
  z.preprocess(blankToUndef, z.coerce.number().min(min).max(max).optional());
export const loginSchema = z.object({ email: z.string().email("Enter a valid email"), password: z.string().min(1, "Enter your password") });

export const registerSchema = z.object({
  full_name: z.string().min(2, "Enter your full name"),
  email: z.string().email("Enter a valid email"),
  phone: z.string().optional(),
  account_type: z.enum(["farmer", "business"]),
  organization: z.string().optional(),
  password: z.string().min(10, "Use at least 10 characters").regex(/[A-Za-z]/, "Include a letter").regex(/\d/, "Include a number"),
});

export const farmSchema = z.object({
  farm_name: z.string().min(2, "Enter a farm name").max(160, "Farm name must be 160 characters or fewer"), location: z.string().optional(),
  area: optNum(0.001, 1_000_000), area_unit: z.enum(["acre", "hectare", "kanal", "marla"]),
});

export const fieldSchema = z.object({
  field_name: z.string().min(1, "Enter a field name"), area: optNum(0.001, 1_000_000), soil_type: z.string().optional(),
  latitude: optNum(-90, 90), longitude: optNum(-180, 180),
});

export const cropSchema = z.object({
  nitrogen: reqNum(0, 300, "Nitrogen"), phosphorus: reqNum(0, 300, "Phosphorus"), potassium: reqNum(0, 300, "Potassium"),
  temperature: reqNum(-10, 55, "Temperature"), humidity: reqNum(0, 100, "Humidity"), ph: reqNum(3, 11, "pH"), rainfall: reqNum(0, 3000, "Rainfall"),
});

export const yieldSchema = z.object({
  crop_name: z.string().min(2, "Choose a crop"), area_ha: reqNum(0.01, 100000, "Area"), rainfall: reqNum(0, 3000, "Rainfall"),
  temperature: reqNum(-10, 55, "Temperature"), irrigated: z.boolean(), fertilizer_kg_ha: reqNum(0, 1500, "Fertilizer"), soil_ph: reqNum(3, 11, "pH"),
});

export const fertilizerSchema = z.object({
  field_id: z.string().optional(),
  crop_name: z.string().min(2, "Choose a crop"), nitrogen: optNum(0, 2000), phosphorus: optNum(0, 2000), potassium: optNum(0, 5000),
  ph: optNum(3, 11),
  growth_stage: z.enum(["sowing", "vegetative", "flowering", "fruiting", "maturity", "harvest"]).optional(),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email"),
});

export const resetPasswordSchema = z.object({
  new_password: z.string()
    .min(10, "Use at least 10 characters")
    .max(128, "Use no more than 128 characters")
    .regex(/[A-Za-z]/, "Include a letter")
    .regex(/\d/, "Include a number"),
  confirm_password: z.string().min(1, "Confirm your password"),
}).refine((v) => v.new_password === v.confirm_password, {
  path: ["confirm_password"],
  message: "Passwords do not match",
});
