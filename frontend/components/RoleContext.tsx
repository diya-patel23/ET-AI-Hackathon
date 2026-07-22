"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type RoleContextType = {
  role: string;
  setRole: (r: string) => void;
};

const RoleContext = createContext<RoleContextType>({ role: "Engineer", setRole: () => {} });

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState("Engineer");
  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export function useRole() {
  return useContext(RoleContext);
}
