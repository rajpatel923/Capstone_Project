"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@clerk/nextjs"
import { toast } from "sonner"
import { itemsApi, redemptionsApi } from "@/lib/api/items"
import type { ItemResponse, ItemCreate, RedemptionCreate, RedemptionResponse } from "@/types/api"
import { APIError } from "@/lib/api/client"

export function useItems() {
  const { getToken } = useAuth()
  const [data, setData] = useState<ItemResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<APIError | null>(null)

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await itemsApi.list(getToken)
      setData(result)
    } catch (e) {
      setError(e as APIError)
    } finally {
      setIsLoading(false)
    }
  }, [getToken])

  useEffect(() => {
    fetch()
  }, [fetch])

  const createItem = async (body: ItemCreate) => {
    const result = await itemsApi.create(getToken, body)
    toast.success(`Item "${result.name}" created`)
    await fetch()
    return result
  }

  const createRedemption = async (body: RedemptionCreate): Promise<RedemptionResponse> => {
    const result = await redemptionsApi.create(getToken, body)
    toast.success(`Redeemed ${result.credits_spent} credits`)
    await fetch()
    return result
  }

  return { data, isLoading, error, createItem, createRedemption, refetch: fetch }
}
