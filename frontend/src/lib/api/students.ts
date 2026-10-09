import { apiFetch } from "./client"
import type {
  StudentListResponse,
  StudentResponse,
  StudentEnrollResponse,
  StudentCreate,
  StudentUpdate,
  LedgerResponse,
} from "@/types/api"

export const studentsApi = {
  list: (getToken: () => Promise<string | null>, cursor?: number) =>
    apiFetch<StudentListResponse>(
      `/students?limit=50${cursor ? `&cursor=${cursor}` : ""}`,
      getToken,
    ),

  create: (getToken: () => Promise<string | null>, body: StudentCreate) =>
    apiFetch<StudentEnrollResponse>("/students", getToken, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  get: (getToken: () => Promise<string | null>, id: number) =>
    apiFetch<StudentResponse>(`/students/${id}`, getToken),

  update: (
    getToken: () => Promise<string | null>,
    id: number,
    body: StudentUpdate,
  ) =>
    apiFetch<StudentResponse>(`/students/${id}`, getToken, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  resetTotp: (getToken: () => Promise<string | null>, id: number) =>
    apiFetch<StudentEnrollResponse>(`/students/${id}/reset-totp`, getToken, {
      method: "POST",
    }),

  getLedger: (getToken: () => Promise<string | null>, id: number) =>
    apiFetch<LedgerResponse>(`/students/${id}/ledger`, getToken),
}
