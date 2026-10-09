import { apiFetch } from "./client"
import type { ItemResponse, ItemCreate, RedemptionResponse, RedemptionCreate } from "@/types/api"

export const itemsApi = {
  list: (getToken: () => Promise<string | null>) =>
    apiFetch<ItemResponse[]>("/items", getToken),

  create: (getToken: () => Promise<string | null>, body: ItemCreate) =>
    apiFetch<ItemResponse>("/items", getToken, {
      method: "POST",
      body: JSON.stringify(body),
    }),
}

export const redemptionsApi = {
  create: (getToken: () => Promise<string | null>, body: RedemptionCreate) =>
    apiFetch<RedemptionResponse>("/redemptions", getToken, {
      method: "POST",
      body: JSON.stringify(body),
    }),
}
