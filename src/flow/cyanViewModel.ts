/**
 * Template variable parser and dynamic handle layout calculator for Red-Cyan
 */

export interface InferredPort {
  id: string;
  name: string;
  topPercent: number;
}

/**
 * Extracts unique port names from prompt template variables matching {{ inputs.<name> }}
 */
export function inferTemplatePorts(templateStr: string): string[] {
  if (!templateStr) return [];
  const pattern = /inputs\.([a-zA-Z0-9_]+)/g;
  const matches = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(templateStr)) !== null) {
    if (match[1]) {
      matches.add(match[1]);
    }
  }
  return Array.from(matches).sort();
}

/**
 * Computes stacked port positions for dynamically inferred handles
 */
export function computeDynamicPortLayouts(portNames: string[]): InferredPort[] {
  if (portNames.length === 0) {
    return [{ id: "in-0", name: "in", topPercent: 50 }];
  }

  return portNames.map((name, index) => {
    const topPercent = ((index + 1) / (portNames.length + 1)) * 100;
    return {
      id: `in-${name}`,
      name,
      topPercent,
    };
  });
}

