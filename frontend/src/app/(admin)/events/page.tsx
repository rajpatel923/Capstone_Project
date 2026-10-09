"use client"

import { useState } from "react"
import { EventsTable } from "@/components/dashboard/events-table"
import { useEvents } from "@/hooks/use-events"
import type { UnlockResult } from "@/types/api"

export default function EventsPage() {
  const [resultFilter, setResultFilter] = useState<UnlockResult | "all">("all")

  const { items, isLoading, hasMore, loadMore } = useEvents({
    result: resultFilter === "all" ? undefined : resultFilter,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Unlock Events</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Full audit log of all access attempts
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4">
        <EventsTable
          events={items}
          loading={isLoading}
          hasMore={hasMore}
          resultFilter={resultFilter}
          onResultFilter={setResultFilter}
          onLoadMore={loadMore}
        />
      </div>
    </div>
  )
}
