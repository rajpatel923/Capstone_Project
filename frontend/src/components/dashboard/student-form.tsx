"use client"

import { useState } from "react"
import { QRCodeSVG } from "qrcode.react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import type { StudentResponse } from "@/types/api"

type Props = {
  open: boolean
  onOpenChange: (v: boolean) => void
  mode: "create" | "edit"
  student?: StudentResponse
  onSubmit: (data: { full_name: string; email: string }) => Promise<{ provisioning_uri?: string }>
}

export function StudentForm({ open, onOpenChange, mode, student, onSubmit }: Props) {
  const [fullName, setFullName] = useState(student?.full_name ?? "")
  const [email, setEmail] = useState(student?.email ?? "")
  const [loading, setLoading] = useState(false)
  const [qrUri, setQrUri] = useState<string | null>(null)

  const isQrStep = qrUri !== null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const result = await onSubmit({ full_name: fullName, email })
      if (result.provisioning_uri) {
        setQrUri(result.provisioning_uri)
      } else {
        handleClose()
      }
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFullName(student?.full_name ?? "")
    setEmail(student?.email ?? "")
    setQrUri(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        {isQrStep ? (
          <>
            <DialogHeader>
              <DialogTitle>Scan TOTP QR Code</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col items-center gap-4 py-4">
              <p className="text-center text-sm text-muted-foreground">
                Have the student scan this QR code with their authenticator app.
                This code is shown once and cannot be retrieved again.
              </p>
              <div className="rounded-lg border bg-white p-4">
                <QRCodeSVG value={qrUri!} size={200} />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  navigator.clipboard.writeText(qrUri!)
                  toast.success("URI copied to clipboard")
                }}
              >
                Copy URI
              </Button>
            </div>
            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>
                {mode === "create" ? "Enroll Student" : "Edit Student"}
              </DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-1.5">
                <label className="text-sm font-medium" htmlFor="full-name">
                  Full Name
                </label>
                <Input
                  id="full-name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  required
                />
              </div>
              <div className="grid gap-1.5">
                <label className="text-sm font-medium" htmlFor="email">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@example.com"
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Saving…" : mode === "create" ? "Enroll" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
