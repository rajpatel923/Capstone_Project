import { apiFetch } from "./client"
import type { UnlockEventListResponse, UnlockResult } from "@/types/api"

export type EventFilters = {
  student_id?: number
  device_id?: number
  result?: UnlockResult
  cursor?: number
}

export const eventsApi = {
  list: (getToken: () => Promise<string | null>, filters: EventFilters = {}) => {
    const params = new URLSearchParams({ limit: "50" })
    if (filters.student_id) params.set("student_id", String(filters.student_id))
    if (filters.device_id) params.set("device_id", String(filters.device_id))
    if (filters.result) params.set("result", filters.result)
    if (filters.cursor) params.set("cursor", String(filters.cursor))
    return apiFetch<UnlockEventListResponse>(
      `/dashboard/unlock-events?${params}`,
      getToken,
    )
  },
}
