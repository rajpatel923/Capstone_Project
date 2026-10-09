"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import type { ItemResponse, StudentResponse, RedemptionCreate } from "@/types/api"

type Props = {
  open: boolean
  onOpenChange: (v: boolean) => void
  items: ItemResponse[]
  students: StudentResponse[]
  onSubmit: (data: RedemptionCreate) => Promise<unknown>
}

export function RedemptionForm({ open, onOpenChange, items, students, onSubmit }: Props) {
  const [studentId, setStudentId] = useState("")
  const [itemId, setItemId] = useState("")
  const [loading, setLoading] = useState(false)

  const selectedItem = items.find((i) => String(i.id) === itemId)
  const selectedStudent = students.find((s) => String(s.id) === studentId)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentId || !itemId) return
    setLoading(true)
    try {
      await onSubmit({ student_id: Number(studentId), item_id: Number(itemId) })
      setStudentId("")
      setItemId("")
      onOpenChange(false)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Process Redemption</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-1.5">
              <label className="text-sm font-medium">Student</label>
              <Select value={studentId} onValueChange={setStudentId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select student" />
                </SelectTrigger>
                <SelectContent>
                  {students.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>
                      <span className="font-mono text-xs">{s.member_id}</span>{" "}
                      {s.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedStudent && (
                <p className="text-xs text-muted-foreground">
                  Member ID: <span className="font-mono">{selectedStudent.member_id}</span>
                </p>
              )}
            </div>
            <div className="grid gap-1.5">
              <label className="text-sm font-medium">Item</label>
              <Select value={itemId} onValueChange={setItemId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select item" />
                </SelectTrigger>
                <SelectContent>
                  {items
                    .filter((i) => i.stock_qty > 0)
                    .map((i) => (
                      <SelectItem key={i.id} value={String(i.id)}>
                        {i.name}{" "}
                        <span className="text-muted-foreground">({i.cost_credits} cr)</span>
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              {selectedItem && (
                <p className="text-xs text-muted-foreground">
                  Cost: <span className="font-mono">{selectedItem.cost_credits}</span> credits
                  · Stock: {selectedItem.stock_qty}
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !studentId || !itemId}>
              {loading ? "Processing…" : "Redeem"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
