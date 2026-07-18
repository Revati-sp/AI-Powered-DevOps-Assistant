"use client";

import * as React from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils/cn";

export interface DataTablePaginationProps {
  pageIndex: number;
  pageSize: number;
  pageCount: number;
  totalRows?: number;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

export interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  pagination?: DataTablePaginationProps;
  emptyMessage?: string;
  className?: string;
}

function DataTable<TData, TValue>({
  columns,
  data,
  pagination,
  emptyMessage = "No results.",
  className,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: Boolean(pagination),
    pageCount: pagination?.pageCount,
  });

  return (
    <div className={cn("space-y-4", className)}>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id} data-state={row.getIsSelected() && "selected"}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {pagination ? (
        <div className="flex items-center justify-between gap-2">
          <p className="text-muted-foreground text-sm">
            {pagination.totalRows != null
              ? `${pagination.totalRows} row(s)`
              : `Page ${pagination.pageIndex + 1} of ${Math.max(pagination.pageCount, 1)}`}
          </p>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => pagination.onPageChange(Math.max(0, pagination.pageIndex - 1))}
              disabled={pagination.pageIndex <= 0}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                pagination.onPageChange(
                  Math.min(Math.max(pagination.pageCount - 1, 0), pagination.pageIndex + 1),
                )
              }
              disabled={pagination.pageIndex >= pagination.pageCount - 1}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export { DataTable };
