import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { ItemResponse } from "@/types/api"

type Props = { items: ItemResponse[]; loading?: boolean }

export function ItemsTable({ items, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Item</TableHead>
          <TableHead className="w-36">Cost (credits)</TableHead>
          <TableHead className="w-28">Stock</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.length === 0 && (
          <TableRow>
            <TableCell colSpan={3} className="py-10 text-center text-sm text-muted-foreground">
              No items yet
            </TableCell>
          </TableRow>
        )}
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-medium">{item.name}</TableCell>
            <TableCell className="font-mono text-sm">{item.cost_credits}</TableCell>
            <TableCell>
              {item.stock_qty === 0 ? (
                <Badge variant="destructive">Out of stock</Badge>
              ) : (
                <span className="text-sm">{item.stock_qty}</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
