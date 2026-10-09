"use client"

import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DeviceTable } from "@/components/dashboard/device-table"
import { useDevices } from "@/hooks/use-devices"

export default function DevicesPage() {
  const { data, isLoading, refetch } = useDevices()
  const onlineCount = data.filter((d) => d.online).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Devices</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {onlineCount} of {data.length} online — auto-refreshes every 30s
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refetch}>
          <RefreshCw className="mr-2 size-4" />
          Refresh
        </Button>
      </div>

      <div className="rounded-lg border bg-white">
        <DeviceTable devices={data} loading={isLoading} />
      </div>
    </div>
  )
}
