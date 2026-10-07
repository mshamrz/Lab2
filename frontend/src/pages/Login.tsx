import { useEffect } from "react";
import { useAuth } from "react-oidc-context";

export default function Login() {
  const auth = useAuth();

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      auth.signinRedirect();
    }
  }, [auth]);

  return <p className="p-10 text-center text-sm text-gray-500">Redirecting to sign in…</p>;
}
