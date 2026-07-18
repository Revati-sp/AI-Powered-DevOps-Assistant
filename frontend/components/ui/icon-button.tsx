import * as React from "react";

import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

export interface IconButtonProps extends Omit<ButtonProps, "size" | "aria-label"> {
  "aria-label": string;
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <Button ref={ref} size="icon" className={cn(className)} {...props}>
        {children}
      </Button>
    );
  },
);
IconButton.displayName = "IconButton";

export { IconButton };
