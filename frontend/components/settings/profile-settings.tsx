"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { PageHeader } from "@/components/data-display/page-header";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchProfile, updateProfile } from "@/features/settings/api";
import { profileSettingsSchema, type ProfileSettingsValues } from "@/features/settings/schemas";
import { queryKeys } from "@/lib/api/query-keys";
import { isApiClientError } from "@/lib/api/errors";
import { useAuth } from "@/providers/auth-provider";

const TIMEZONES = [
  "UTC",
  "America/Los_Angeles",
  "America/Denver",
  "America/Chicago",
  "America/New_York",
  "America/Sao_Paulo",
  "Europe/London",
  "Europe/Berlin",
  "Asia/Kolkata",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Australia/Sydney",
];

const initials = (value: string) =>
  value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

export function ProfileSettings() {
  const { refreshUser } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.auth.currentUser(),
    queryFn: fetchProfile,
  });
  const form = useForm<ProfileSettingsValues>({
    resolver: zodResolver(profileSettingsSchema),
    defaultValues: { display_name: "", username: "", timezone: "UTC", job_title: "", avatar_url: "" },
  });

  useEffect(() => {
    if (data) {
      form.reset({
        display_name: data.display_name ?? "",
        username: data.username,
        timezone: data.timezone ?? "UTC",
        job_title: data.job_title ?? "",
        avatar_url: data.avatar_url ?? "",
      });
    }
  }, [data, form]);

  const updateMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.currentUser() });
      await refreshUser();
      toast.success("Profile updated");
    },
    onError: (mutationError) => {
      toast.error(isApiClientError(mutationError) ? mutationError.message : "Failed to update profile");
    },
  });

  if (isLoading) {
    return <LoadingState label="Loading profile…" />;
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={isApiClientError(error) ? error.message : "Failed to load profile"}
        requestId={isApiClientError(error) ? error.requestId : undefined}
        onRetry={() => void refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Manage the details visible to your workspace." />
      <div className="flex max-w-2xl items-center gap-4 rounded-lg border p-4">
        <Avatar className="h-16 w-16">
          <AvatarImage src={data.avatar_url ?? undefined} alt="" />
          <AvatarFallback>{initials(data.display_name || data.username)}</AvatarFallback>
        </Avatar>
        <div>
          <p className="font-medium">{data.display_name || data.username}</p>
          <p className="text-muted-foreground text-sm">{data.email}</p>
        </div>
      </div>
      <Form {...form}>
        <form
          className="grid max-w-2xl gap-4 sm:grid-cols-2"
          onSubmit={form.handleSubmit((values) =>
            updateMutation.mutate({
              username: values.username,
              display_name: values.display_name || null,
              timezone: values.timezone || null,
              job_title: values.job_title || null,
              avatar_url: values.avatar_url || null,
            }),
          )}
        >
          <FormField control={form.control} name="display_name" render={({ field }) => (
            <FormItem><FormLabel>Display name</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
          )} />
          <FormField control={form.control} name="username" render={({ field }) => (
            <FormItem><FormLabel>Username</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
          )} />
          <FormItem><FormLabel>Email</FormLabel><FormControl><Input value={data.email} readOnly disabled /></FormControl></FormItem>
          <FormField control={form.control} name="timezone" render={({ field }) => (
            <FormItem><FormLabel>Timezone</FormLabel><Select value={field.value || "UTC"} onValueChange={field.onChange}><FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl><SelectContent>{TIMEZONES.map((timezone) => <SelectItem key={timezone} value={timezone}>{timezone}</SelectItem>)}</SelectContent></Select><FormMessage /></FormItem>
          )} />
          <FormField control={form.control} name="job_title" render={({ field }) => (
            <FormItem><FormLabel>Job title</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>
          )} />
          <FormField control={form.control} name="avatar_url" render={({ field }) => (
            <FormItem><FormLabel>Avatar URL</FormLabel><FormControl><Input placeholder="https://…" {...field} /></FormControl><FormMessage /></FormItem>
          )} />
          <div className="col-span-full flex justify-end gap-2">
            <Button type="button" variant="outline" disabled={!form.formState.isDirty || updateMutation.isPending} onClick={() => form.reset()}>Cancel</Button>
            <Button type="submit" disabled={!form.formState.isDirty || updateMutation.isPending}>{updateMutation.isPending ? "Saving…" : "Save changes"}</Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
