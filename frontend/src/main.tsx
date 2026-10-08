import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "react-oidc-context";

import App from "./App";
import Login from "./pages/Login";
import Callback from "./pages/Callback";
import "./index.css";

const cognitoAuthConfig = {
  authority: "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_zous9WTDf",
  client_id: "c76j5carht9ilqha454ioj3hm",
  redirect_uri: "https://d30mlui26iqxfd.cloudfront.net/auth/callback/",
  scope: "openid email profile",
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider {...cognitoAuthConfig}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/login/" element={<Login />} />
          <Route path="/auth/callback/" element={<Callback />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
);
