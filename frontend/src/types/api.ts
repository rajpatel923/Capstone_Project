export type StudentResponse = {
  id: number
  member_id: string
  full_name: string
  email: string
  active: boolean
  created_at: string
}

export type StudentEnrollResponse = StudentResponse & {
  provisioning_uri: string
}

export type StudentListResponse = {
  items: StudentResponse[]
  next_cursor: number | null
}

export type StudentCreate = {
  full_name: string
  email: string
}

export type StudentUpdate = {
  full_name?: string
  email?: string
  active?: boolean
}

export type UnlockResult =
  | "granted"
  | "invalid_format"
  | "unknown_member"
  | "invalid_totp"
  | "no_eligibility"
  | "member_inactive"
  | "forced_open"

export type UnlockEventResponse = {
  id: number
  device_id: number
  student_id: number | null
  member_id_raw: string
  result: UnlockResult
  created_at: string
}

export type UnlockEventListResponse = {
  items: UnlockEventResponse[]
  next_cursor: number | null
}

export type DeviceResponse = {
  id: number
  device_name: string
  firmware_version: string | null
  last_seen_at: string | null
  online: boolean
}

export type ItemResponse = {
  id: number
  name: string
  cost_credits: number
  stock_qty: number
}

export type ItemCreate = {
  name: string
  cost_credits: number
  stock_qty: number
}

export type LedgerEntry = {
  id: number
  delta: number
  reason: string
  challenge_id: number | null
  redemption_id: number | null
  created_at: string
}

export type LedgerResponse = {
  student_id: number
  balance: number
  entries: LedgerEntry[]
}

export type RedemptionResponse = {
  id: number
  student_id: number
  item_id: number
  credits_spent: number
  created_at: string
}

export type RedemptionCreate = {
  student_id: number
  item_id: number
}
