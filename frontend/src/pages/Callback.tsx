import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "react-oidc-context";

export default function Callback() {
  const auth = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.isAuthenticated) {
      navigate("/");
    }
  }, [auth.isAuthenticated, navigate]);

  if (auth.error) {
    return <p className="p-10 text-center text-sm text-red-600">Sign-in error: {auth.error.message}</p>;
  }

  return <p className="p-10 text-center text-sm text-gray-500">Signing you in…</p>;
}
