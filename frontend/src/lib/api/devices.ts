import { apiFetch } from "./client"
import type { DeviceResponse } from "@/types/api"

export const devicesApi = {
  list: (getToken: () => Promise<string | null>) =>
    apiFetch<DeviceResponse[]>("/devices", getToken),
}
