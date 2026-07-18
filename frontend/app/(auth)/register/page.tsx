import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">Create account</h1>
        <p className="text-muted-foreground text-sm">
          Register to start analyzing logs, generating infra, and chatting with your assistant.
        </p>
      </div>
      <RegisterForm />
    </div>
  );
}
