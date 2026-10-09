"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@clerk/nextjs"
import { devicesApi } from "@/lib/api/devices"
import type { DeviceResponse } from "@/types/api"
import { APIError } from "@/lib/api/client"

export function useDevices() {
  const { getToken } = useAuth()
  const [data, setData] = useState<DeviceResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<APIError | null>(null)

  const fetch = useCallback(async () => {
    setError(null)
    try {
      const result = await devicesApi.list(getToken)
      setData(result)
    } catch (e) {
      setError(e as APIError)
    } finally {
      setIsLoading(false)
    }
  }, [getToken])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, 30_000)
    return () => clearInterval(id)
  }, [fetch])

  return { data, isLoading, error, refetch: fetch }
}
