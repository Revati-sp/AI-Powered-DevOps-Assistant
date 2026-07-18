"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import * as React from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  organizationFormSchema,
  type OrganizationFormValues,
} from "@/features/organizations/schemas";
import { slugify } from "@/features/organizations/slugify";
import type { OrganizationResponse } from "@/features/organizations/types";

type OrganizationFormDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  initial?: OrganizationResponse | null;
  loading?: boolean;
  onSubmit: (values: OrganizationFormValues) => Promise<void> | void;
};

export function OrganizationFormDialog({
  open,
  onOpenChange,
  title,
  description,
  initial,
  loading = false,
  onSubmit,
}: OrganizationFormDialogProps) {
  const form = useForm<OrganizationFormValues>({
    resolver: zodResolver(organizationFormSchema),
    defaultValues: {
      name: initial?.name ?? "",
      slug: initial?.slug ?? "",
    },
  });

  React.useEffect(() => {
    if (open) {
      form.reset({
        name: initial?.name ?? "",
        slug: initial?.slug ?? "",
      });
    }
  }, [open, initial, form]);

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit({
      name: values.name,
      slug: values.slug?.trim() ? values.slug.trim() : undefined,
    });
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      disabled={loading}
                      onChange={(event) => {
                        field.onChange(event);
                        if (!initial && !form.formState.dirtyFields.slug) {
                          form.setValue("slug", slugify(event.target.value), {
                            shouldValidate: true,
                          });
                        }
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="slug"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Slug</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      value={field.value ?? ""}
                      disabled={loading}
                      placeholder="optional-url-slug"
                    />
                  </FormControl>
                  <FormDescription>
                    Lowercase letters, numbers, and hyphens. Leave blank to auto-generate.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                disabled={loading}
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
