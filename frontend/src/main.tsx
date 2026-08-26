import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import "./styles/tokens.css";
import "./styles/global.css";
import { App } from "./App";

const queryClient = new QueryClient();
ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><App queryClient={queryClient} /></BrowserRouter></QueryClientProvider></React.StrictMode>);
