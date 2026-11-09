import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";
import { BrandMark, Wordmark } from "../../../components/ui/BrandMark";
import { Button, buttonClass } from "../../../components/ui/Button";
import { ErrorSummary, Notice } from "../../../components/ui/Feedback";
import { Field } from "../../../components/ui/Field";
import { apiUrl } from "../../../lib/api-client";
import { errorsByPath, generalError, summaryErrors } from "../../../lib/form";
import { vi } from "../../../locales/vi";
import { useLogin, useRegister } from "../api/auth";

type AuthMode = "login" | "register";

type AuthPageProps = {
  mode: AuthMode;
};

function GoogleGlyph() {
  return (
    <svg
      className="auth-google-glyph"
      viewBox="0 0 48 48"
      width="18"
      height="18"
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  );
}

const FIELD_IDS: Record<string, string> = {
  email: "auth-email",
  password: "auth-password",
  display_name: "auth-display-name",
};

const DEFAULT_TARGET = "/demand";

export function AuthPage({ mode }: AuthPageProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const register = useRegister();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const isRegister = mode === "register";
  const mutation = isRegister ? register : login;
  const errors = errorsByPath(mutation.error);
  const general = generalError(mutation.error);
  const target = (location.state as { from?: string } | null)?.from ?? DEFAULT_TARGET;
  const [searchParams] = useSearchParams();
  const googleError = searchParams.get("error");
  const googleMessage = googleError
    ? (vi.auth.googleErrors as Record<string, string>)[googleError]
    : undefined;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const credentials = { email, password };
    const options = { onSuccess: () => navigate(target, { replace: true }) };
    if (isRegister) {
      register.mutate({ ...credentials, display_name: displayName }, options);
    } else {
      login.mutate(credentials, options);
    }
  }

  return (
    <section className="auth-page" aria-labelledby="auth-title">
      <Link to="/" className="brand auth-brand">
        <BrandMark />
        <Wordmark />
      </Link>
      <div className="auth-panel blueprint">
        <h1 id="auth-title" className="auth-title">
          {isRegister ? vi.auth.registerTitle : vi.auth.loginTitle}
        </h1>
        <p className="auth-lead">{isRegister ? vi.auth.registerLead : vi.auth.loginLead}</p>
        <form className="form-stack" onSubmit={handleSubmit} noValidate>
          <ErrorSummary
            errors={summaryErrors(mutation.error, (path) => FIELD_IDS[path.split(".")[0] ?? ""])}
          />
          {general && <Notice kind="error" title={general} />}
          {!general && googleMessage && <Notice kind="error" title={googleMessage} />}
          {isRegister && (
            <Field
              id={FIELD_IDS.display_name}
              label={vi.auth.displayName}
              error={errors.get("display_name")}
            >
              {(control) => (
                <input
                  {...control}
                  className="input"
                  value={displayName}
                  maxLength={120}
                  autoComplete="name"
                  onChange={(event) => setDisplayName(event.target.value)}
                />
              )}
            </Field>
          )}
          <Field id={FIELD_IDS.email} label={vi.auth.email} error={errors.get("email")}>
            {(control) => (
              <input
                {...control}
                className="input"
                type="email"
                value={email}
                maxLength={254}
                autoComplete="email"
                onChange={(event) => setEmail(event.target.value)}
              />
            )}
          </Field>
          <Field
            id={FIELD_IDS.password}
            label={vi.auth.password}
            hint={isRegister ? vi.auth.passwordHint : undefined}
            error={errors.get("password")}
          >
            {(control) => (
              <input
                {...control}
                className="input"
                type="password"
                value={password}
                maxLength={128}
                autoComplete={isRegister ? "new-password" : "current-password"}
                onChange={(event) => setPassword(event.target.value)}
              />
            )}
          </Field>
          <Button type="submit" variant="primary" disabled={mutation.isPending}>
            {mutation.isPending
              ? vi.common.saving
              : isRegister
                ? vi.auth.submitRegister
                : vi.auth.submitLogin}
          </Button>
        </form>
        <div className="auth-divider">
          <span>{vi.auth.or}</span>
        </div>
        <a
          className={`${buttonClass("secondary")} auth-google`}
          href={apiUrl("/auth/google/start")}
        >
          <GoogleGlyph />
          {vi.auth.googleContinue}
        </a>
        <p className="auth-switch">
          <Link to={isRegister ? "/login" : "/register"}>
            {isRegister ? vi.auth.switchToLogin : vi.auth.switchToRegister}
          </Link>
        </p>
      </div>
    </section>
  );
}
