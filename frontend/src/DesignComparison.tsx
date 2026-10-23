import { designOptions, useDesignVariant, designPreviewUrl } from "./designPreview";
export default function DesignComparison() {
  const designVariant = useDesignVariant();
  return <nav className="design-comparison" aria-label="Compare application designs">
    <span>Design preview</span><div>
      {designOptions.map(option => <a key={option.id} href={designPreviewUrl(option.id)} aria-current={designVariant === option.id ? "page" : undefined}>{option.label}</a>)}
    </div>
  </nav>;
}
