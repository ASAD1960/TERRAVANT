export interface User {
  id: string; full_name: string; email: string; phone: string | null; organization: string | null;
  language: string; status: string; role_names: string[]; created_at: string;
}
export interface Field { id: string; farm_id: string; field_name: string; area: number | null; soil_type: string | null; latitude: number | null; longitude: number | null; current_crop_id: string | null }
export interface Farm { id: string; owner_id: string; farm_name: string; location: string | null; area: number | null; area_unit: string; created_at: string }
export interface FarmDetail extends Farm { fields: Field[] }
export interface Alternative { label: string; probability: number }
export interface CropResult {
  prediction_id: string; predicted_crop: string; confidence: number; alternatives: Alternative[];
  explanation: { method: string; top_factors: { feature: string; importance: number; value: number; deviation_from_typical: number }[] };
  model_version: string; data_source: string; limitations: string[];
}
export interface DiseaseResult {
  prediction_id: string; predicted_class: string; confidence: number; is_uncertain: boolean; alternatives: Alternative[];
  model_version: string; data_source: string; message: string; limitations: string[];
}
export interface YieldResult {
  prediction_id: string; crop_name: string; yield_per_ha: number; yield_low: number; yield_high: number; total_production: number;
  yield_unit: string; interval_note: string; model_version: string; data_source: string; limitations: string[];
}
export interface FertilizerResult {
  recommendation_id: string; crop_name: string; nutrient_status: Record<string, { value: number; status: string; reference_range: [number, number] }>;
  ph_status: { value: number; status: string; note: string } | null; guidance: string[]; needs_lab_test: boolean; lab_test_reasons: string[];
  ruleset_version: string; disclaimer: string;
}
export interface Dashboard {
  total_farms: number; total_area: number; area_unit: string; total_fields: number; prediction_counts: { crop: number; disease: number; yield: number };
  recent_predictions: { type: string; id: string; summary: string; created_at: string }[]; unread_notifications: number;
}
export interface WeatherForecast {
  source: string; stale: boolean; latitude: number; longitude: number;
  current: { temperature_c: number | null; humidity_pct: number | null; precipitation_mm: number | null; wind_kmh: number | null };
  forecast: { date: string; t_max: number; t_min: number; rain_mm: number; rain_prob_pct: number | null }[]; advisories: string[];
}
export interface NotificationItem { id: string; title: string; message: string; is_read: boolean; created_at: string }
export interface Crop { id: string; crop_name: string; category: string | null; growing_season: string | null }

