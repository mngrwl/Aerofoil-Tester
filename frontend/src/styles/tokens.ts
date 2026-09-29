import { css } from 'lit';

/** Shared visual rules keep screen components focused on their own content. */
export const tokens = css`
  :host {
    --canvas: #f6f7f5;
    --surface: #ffffff;
    --ink: #15201c;
    --muted-ink: #5d6862;
    --line: #d8ddd9;
    --action: #165941;
    --action-hover: #0f4934;
    --error: #a32d20;
    --space-1: 0.5rem;
    --space-2: 0.75rem;
    --space-3: 1rem;
    --space-4: 1.5rem;
    --space-5: 2.25rem;
    --space-6: 4rem;
    --radius: 0.5rem;
  }
`;
