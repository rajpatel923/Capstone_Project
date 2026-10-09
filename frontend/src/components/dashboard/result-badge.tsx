import { Badge } from "@/components/ui/badge"
import { cn } from "cn"
import type { UnlockResult } from "@/types/api"

type Config = {
  label: string
  variant: "default" | "secondary" | "destructive" | "outline"
  dot: string
}

const RESULT_CONFIG: Record<UnlockResult, Config> = {
  granted: { label: "Granted", variant: "default", dot: "bg-green-500" },
  forced_open: { label: "Forced Open", variant: "destructive", dot: "bg-red-500" },
  invalid_totp: { label: "Invalid TOTP", variant: "secondary", dot: "bg-yellow-500" },
  no_eligibility: { label: "No Eligibility", variant: "secondary", dot: "bg-yellow-500" },
  unknown_member: { label: "Unknown Member", variant: "outline", dot: "bg-orange-400" },
  member_inactive: { label: "Inactive Member", variant: "outline", dot: "bg-zinc-400" },
  invalid_format: { label: "Invalid Format", variant: "outline", dot: "bg-zinc-400" },
}

export function ResultBadge({ result }: { result: UnlockResult }) {
  const cfg = RESULT_CONFIG[result] ?? {
    label: result,
    variant: "outline" as const,
    dot: "bg-zinc-400",
  }
  return (
    <Badge variant={cfg.variant} className="gap-1.5">
      <span className={cn("size-1.5 shrink-0 rounded-full", cfg.dot)} />
      {cfg.label}
    </Badge>
  )
}
