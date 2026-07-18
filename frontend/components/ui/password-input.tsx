"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";

import { IconButton } from "@/components/ui/icon-button";
import { Input, type InputProps } from "@/components/ui/input";
import { cn } from "@/lib/utils/cn";

export type PasswordInputProps = Omit<InputProps, "type">;

const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, ...props }, ref) => {
    const [visible, setVisible] = React.useState(false);

    return (
      <div className="relative">
        <Input
          ref={ref}
          type={visible ? "text" : "password"}
          className={cn("pr-10", className)}
          {...props}
        />
        <IconButton
          type="button"
          variant="ghost"
          aria-label={visible ? "Hide password" : "Show password"}
          className="absolute top-1/2 right-1 h-7 w-7 -translate-y-1/2"
          onClick={() => setVisible((v) => !v)}
        >
          {visible ? <EyeOff /> : <Eye />}
        </IconButton>
      </div>
    );
  },
);
PasswordInput.displayName = "PasswordInput";

export { PasswordInput };
