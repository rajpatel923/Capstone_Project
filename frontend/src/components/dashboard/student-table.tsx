"use client"

import { useRouter } from "next/navigation"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { MoreHorizontal } from "lucide-react"
import type { StudentResponse } from "@/types/api"

type Props = {
  students: StudentResponse[]
  loading?: boolean
  onEdit: (student: StudentResponse) => void
  onToggleActive: (student: StudentResponse) => void
  onResetTotp: (student: StudentResponse) => void
}

export function StudentTable({ students, loading, onEdit, onToggleActive, onResetTotp }: Props) {
  const router = useRouter()

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-28">Member ID</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead className="w-24">Status</TableHead>
          <TableHead className="w-36">Enrolled</TableHead>
          <TableHead className="w-10" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {students.length === 0 && (
          <TableRow>
            <TableCell colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
              No students yet
            </TableCell>
          </TableRow>
        )}
        {students.map((s) => (
          <TableRow
            key={s.id}
            className="cursor-pointer"
            onClick={() => router.push(`/students/${s.id}`)}
          >
            <TableCell className="font-mono text-xs">{s.member_id}</TableCell>
            <TableCell className="font-medium">{s.full_name}</TableCell>
            <TableCell className="text-sm text-muted-foreground">{s.email}</TableCell>
            <TableCell>
              <Badge variant={s.active ? "default" : "outline"}>
                {s.active ? "Active" : "Inactive"}
              </Badge>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {new Date(s.created_at).toLocaleDateString()}
            </TableCell>
            <TableCell onClick={(e) => e.stopPropagation()}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="size-7">
                    <MoreHorizontal className="size-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => router.push(`/students/${s.id}`)}>
                    View details
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit(s)}>Edit</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onToggleActive(s)}>
                    {s.active ? "Deactivate" : "Activate"}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onResetTotp(s)}>
                    Reset TOTP
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
