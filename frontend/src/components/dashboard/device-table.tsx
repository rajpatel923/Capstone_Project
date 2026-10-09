import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "cn"
import type { DeviceResponse } from "@/types/api"

function relativeTime(iso: string | null): string {
  if (!iso) return "Never"
  const diff = Date.now() - new Date(iso).getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  return `${h}h ago`
}

type Props = { devices: DeviceResponse[]; loading?: boolean }

export function DeviceTable({ devices, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Device</TableHead>
          <TableHead className="w-40">Firmware</TableHead>
          <TableHead className="w-36">Last Seen</TableHead>
          <TableHead className="w-24">Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {devices.length === 0 && (
          <TableRow>
            <TableCell colSpan={4} className="py-10 text-center text-sm text-muted-foreground">
              No devices registered
            </TableCell>
          </TableRow>
        )}
        {devices.map((d) => (
          <TableRow key={d.id}>
            <TableCell className="font-medium">{d.device_name}</TableCell>
            <TableCell className="font-mono text-xs text-muted-foreground">
              {d.firmware_version ?? "—"}
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {relativeTime(d.last_seen_at)}
            </TableCell>
            <TableCell>
              <span className="flex items-center gap-2 text-sm">
                <span
                  className={cn(
                    "size-2 rounded-full",
                    d.online ? "animate-pulse bg-green-500" : "bg-zinc-400",
                  )}
                />
                {d.online ? "Online" : "Offline"}
              </span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
