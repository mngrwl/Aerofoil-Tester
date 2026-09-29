import { LitElement, html } from 'lit';
import { customElement } from 'lit/decorators.js';

import '../features/project-setup/project-setup.js';

/** The application shell will own screen navigation as more workflow stages are added. */
@customElement('aerofoil-app')
export class AerofoilApp extends LitElement {
  override createRenderRoot(): this {
    return this;
  }

  override render() {
    return html`<aerofoil-project-setup></aerofoil-project-setup>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'aerofoil-app': AerofoilApp;
  }
}
