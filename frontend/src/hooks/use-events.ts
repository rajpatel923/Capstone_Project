"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@clerk/nextjs"
import { eventsApi, type EventFilters } from "@/lib/api/events"
import type { UnlockEventResponse } from "@/types/api"
import { APIError } from "@/lib/api/client"

export function useEvents(filters: Omit<EventFilters, "cursor"> = {}) {
  const { getToken } = useAuth()
  const [items, setItems] = useState<UnlockEventResponse[]>([])
  const [cursor, setCursor] = useState<number | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<APIError | null>(null)

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await eventsApi.list(getToken, filters)
      setItems(result.items)
      setCursor(result.next_cursor)
      setHasMore(result.next_cursor !== null)
    } catch (e) {
      setError(e as APIError)
    } finally {
      setIsLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getToken, filters.student_id, filters.device_id, filters.result])

  useEffect(() => {
    fetch()
  }, [fetch])

  const loadMore = async () => {
    if (!cursor) return
    try {
      const result = await eventsApi.list(getToken, { ...filters, cursor })
      setItems((prev) => [...prev, ...result.items])
      setCursor(result.next_cursor)
      setHasMore(result.next_cursor !== null)
    } catch (e) {
      setError(e as APIError)
    }
  }

  return { items, isLoading, error, hasMore, loadMore, refetch: fetch }
}
