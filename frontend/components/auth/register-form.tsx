"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
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
import { PasswordInput } from "@/components/ui/password-input";
import { registerRequest } from "@/features/auth/api";
import { registerSchema, type RegisterFormValues } from "@/features/auth/schemas";
import { isApiClientError } from "@/lib/api/errors";
import { PASSWORD_MIN } from "@/lib/constants/app";

export function RegisterForm() {
  const router = useRouter();
  const [formError, setFormError] = React.useState<string | null>(null);

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      username: "",
      password: "",
    },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setFormError(null);
    try {
      await registerRequest(values);
      toast.success("Account created", {
        description: "You can sign in with your new credentials.",
      });
      router.push("/login");
    } catch (error) {
      if (isApiClientError(error) && error.status === 429) {
        setFormError("Too many attempts. Please try again later.");
        return;
      }
      if (isApiClientError(error) && error.status === 409) {
        setFormError(error.message || "An account with those details already exists.");
        return;
      }
      setFormError(
        isApiClientError(error) ? error.message : "Registration failed. Please try again.",
      );
    }
  });

  const isSubmitting = form.formState.isSubmitting;

  return (
    <Form {...form}>
      <form onSubmit={onSubmit} className="space-y-5" noValidate>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.com"
                  disabled={isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input
                  autoComplete="username"
                  placeholder="your-username"
                  disabled={isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <PasswordInput
                  autoComplete="new-password"
                  placeholder="••••••••••••"
                  disabled={isSubmitting}
                  {...field}
                />
              </FormControl>
              <FormDescription>At least {PASSWORD_MIN} characters.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {formError ? (
          <p
            role="alert"
            className="bg-destructive/10 text-destructive rounded-md px-3 py-2 text-sm"
          >
            {formError}
          </p>
        ) : null}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Creating account…" : "Create account"}
        </Button>

        <p className="text-muted-foreground text-center text-sm">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-primary font-medium underline-offset-4 hover:underline"
          >
            Sign in
          </Link>
        </p>
      </form>
    </Form>
  );
}
