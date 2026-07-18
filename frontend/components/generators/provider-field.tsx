"use client";

import type { FieldValues, Path, UseFormReturn } from "react-hook-form";

import { FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LLM_PROVIDERS } from "@/lib/constants/app";

type ProviderFieldProps<T extends FieldValues> = {
  form: UseFormReturn<T>;
  name?: Path<T>;
};

export function ProviderField<T extends FieldValues>({
  form,
  name = "provider" as Path<T>,
}: ProviderFieldProps<T>) {
  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>Provider</FormLabel>
          <Select value={String(field.value)} onValueChange={field.onChange}>
            <FormControl>
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {LLM_PROVIDERS.map((provider) => (
                <SelectItem key={provider} value={provider}>
                  {provider}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
