"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@clerk/nextjs"
import { studentsApi } from "@/lib/api/students"
import type { StudentResponse, LedgerResponse } from "@/types/api"
import { APIError } from "@/lib/api/client"

export function useStudent(id: number) {
  const { getToken } = useAuth()
  const [student, setStudent] = useState<StudentResponse | null>(null)
  const [ledger, setLedger] = useState<LedgerResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<APIError | null>(null)

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [s, l] = await Promise.all([
        studentsApi.get(getToken, id),
        studentsApi.getLedger(getToken, id),
      ])
      setStudent(s)
      setLedger(l)
    } catch (e) {
      setError(e as APIError)
    } finally {
      setIsLoading(false)
    }
  }, [getToken, id])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { student, ledger, isLoading, error, refetch: fetch }
}
