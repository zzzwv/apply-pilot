import { Layout } from "antd";
import type { QueryClient } from "@tanstack/react-query";
import { Link, NavLink } from "react-router-dom";

import logo from "../../assets/brand/applypilot-mark.svg";
import { AuthControls } from "../AuthControls";

type Props = {
  queryClient?: QueryClient;
};

export function AppHeader({ queryClient }: Props) {
  return (
    <Layout.Header className="applypilot-header">
      <div className="applypilot-header__inner">
        <Link className="applypilot-header__brand" to="/" aria-label="ApplyPilot 首页">
          <img src={logo} alt="ApplyPilot" />
          <span>
            <strong>ApplyPilot</strong>
            <p>秋招 / 实习投递管理</p>
          </span>
        </Link>
        <nav className="applypilot-header__nav" aria-label="主导航">
          <NavLink to="/" end>数据看板</NavLink>
          <NavLink to="/applications">投递记录</NavLink>
        </nav>
        <div className="applypilot-header__auth" aria-label="账户操作">
          {queryClient && <AuthControls queryClient={queryClient} />}
        </div>
      </div>
    </Layout.Header>
  );
}
