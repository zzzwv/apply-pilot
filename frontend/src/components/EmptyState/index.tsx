import type { ReactNode } from "react";

type EmptyStateImage = {
  src: string;
  alt: string;
};

type EmptyStateProps = {
  image: EmptyStateImage;
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ image, title, description, action }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <img className="empty-state__image" src={image.src} alt={image.alt} />
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__description">{description}</p>
      {action && <div className="empty-state__action">{action}</div>}
    </section>
  );
}
