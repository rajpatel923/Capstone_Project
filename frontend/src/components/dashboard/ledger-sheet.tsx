import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "cn"
import type { LedgerResponse } from "@/types/api"

type Props = {
  open: boolean
  onOpenChange: (v: boolean) => void
  ledger: LedgerResponse | null
  studentName?: string
}

export function LedgerSheet({ open, onOpenChange, ledger, studentName }: Props) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Credit Ledger — {studentName}</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Balance */}
          <div className="rounded-lg border bg-muted/40 px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Balance</p>
            <p className="mt-1 text-3xl font-bold">
              {ledger?.balance ?? "—"}
              <span className="ml-1 text-sm font-normal text-muted-foreground">credits</span>
            </p>
          </div>

          {/* Entries */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-20">Delta</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead className="w-36">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(ledger?.entries ?? []).length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                    No transactions
                  </TableCell>
                </TableRow>
              )}
              {(ledger?.entries ?? []).map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell
                    className={cn(
                      "font-mono text-sm font-semibold",
                      entry.delta > 0 ? "text-green-600" : "text-red-500",
                    )}
                  >
                    {entry.delta > 0 ? `+${entry.delta}` : entry.delta}
                  </TableCell>
                  <TableCell className="text-sm capitalize">
                    {entry.reason.replace(/_/g, " ")}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(entry.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </SheetContent>
    </Sheet>
  )
}
