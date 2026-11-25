import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";
import type { Crop, Field } from "../types";

export const useFields = () => useQuery({ queryKey: ["fields"], queryFn: () => api<Field[]>("/fields") });
export const useCrops = () => useQuery({ queryKey: ["crops"], queryFn: () => api<Crop[]>("/crops"), staleTime: 3_600_000 });
