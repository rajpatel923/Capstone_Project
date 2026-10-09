"use client"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ResultBadge } from "./result-badge"
import type { UnlockEventResponse, UnlockResult } from "@/types/api"

const RESULT_OPTIONS: { value: UnlockResult | "all"; label: string }[] = [
  { value: "all", label: "All results" },
  { value: "granted", label: "Granted" },
  { value: "invalid_totp", label: "Invalid TOTP" },
  { value: "no_eligibility", label: "No Eligibility" },
  { value: "unknown_member", label: "Unknown Member" },
  { value: "member_inactive", label: "Inactive Member" },
  { value: "invalid_format", label: "Invalid Format" },
  { value: "forced_open", label: "Forced Open" },
]

type Props = {
  events: UnlockEventResponse[]
  loading?: boolean
  hasMore?: boolean
  resultFilter?: UnlockResult | "all"
  onResultFilter: (v: UnlockResult | "all") => void
  onLoadMore: () => void
}

export function EventsTable({
  events,
  loading,
  hasMore,
  resultFilter = "all",
  onResultFilter,
  onLoadMore,
}: Props) {
  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3">
        <Select value={resultFilter} onValueChange={(v) => onResultFilter(v as UnlockResult | "all")}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by result" />
          </SelectTrigger>
          <SelectContent>
            {RESULT_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">ID</TableHead>
                <TableHead className="w-32">Member ID</TableHead>
                <TableHead className="w-24">Device</TableHead>
                <TableHead className="w-48">Result</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-sm text-muted-foreground">
                    No events found
                  </TableCell>
                </TableRow>
              )}
              {events.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {e.id}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{e.member_id_raw}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    #{e.device_id}
                  </TableCell>
                  <TableCell>
                    <ResultBadge result={e.result} />
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(e.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {hasMore && (
            <div className="flex justify-center pt-2">
              <Button variant="outline" size="sm" onClick={onLoadMore}>
                Load more
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
