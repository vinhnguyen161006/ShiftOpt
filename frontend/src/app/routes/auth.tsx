import { AuthPage } from "../../features/auth/components/AuthPage";

export function LoginRoute() {
  return <AuthPage mode="login" />;
}

export function RegisterRoute() {
  return <AuthPage mode="register" />;
}
