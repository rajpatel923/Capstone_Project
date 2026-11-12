"use client"

import { useState } from "react"
import { Plus, ShoppingCart } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ItemsTable } from "@/components/dashboard/items-table"
import { ItemForm } from "@/components/dashboard/item-form"
import { RedemptionForm } from "@/components/dashboard/redemption-form"
import { useItems } from "@/hooks/use-items"
import { useStudents } from "@/hooks/use-students"

export default function ItemsPage() {
  const { data: items, isLoading, error, createItem, createRedemption } = useItems()
  const { data: studentsData } = useStudents()
  const [itemFormOpen, setItemFormOpen] = useState(false)
  const [redemptionFormOpen, setRedemptionFormOpen] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Items</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {items.length} items in inventory
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setRedemptionFormOpen(true)}>
            <ShoppingCart className="mr-2 size-4" />
            Process Redemption
          </Button>
          <Button onClick={() => setItemFormOpen(true)}>
            <Plus className="mr-2 size-4" />
            Add Item
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load data: {error.message}
        </div>
      )}

      <div className="rounded-lg border bg-white">
        <ItemsTable items={items} loading={isLoading} />
      </div>

      <ItemForm
        open={itemFormOpen}
        onOpenChange={setItemFormOpen}
        onSubmit={createItem}
      />

      <RedemptionForm
        open={redemptionFormOpen}
        onOpenChange={setRedemptionFormOpen}
        items={items}
        students={studentsData?.items ?? []}
        onSubmit={createRedemption}
      />
    </div>
  )
}
