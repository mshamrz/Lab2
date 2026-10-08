import { useEffect } from "react";
import { useAuth } from "react-oidc-context";

export default function Login() {
  const auth = useAuth();

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated && !auth.error) {
      auth.signinRedirect();
    }
  }, [auth]);

  return (
    <div className="p-10 text-center text-sm text-gray-500">
      <p>isLoading: {String(auth.isLoading)}</p>
      <p>isAuthenticated: {String(auth.isAuthenticated)}</p>
      <p>error: {auth.error ? auth.error.message : "none"}</p>
      <p>activeNavigator: {String(auth.activeNavigator)}</p>
    </div>
  );
}
