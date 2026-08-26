import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description?: string;
  extra?: ReactNode;
};

export function PageHeader({ title, description, extra }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <h1 className="page-header__title">{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {extra && <div className="page-header__extra">{extra}</div>}
    </header>
  );
}
