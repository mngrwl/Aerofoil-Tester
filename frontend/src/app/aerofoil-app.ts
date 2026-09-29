import { LitElement, html } from 'lit';
import { customElement } from 'lit/decorators.js';

import '../features/start-design/start-design-screen.js';

/** The application shell will own screen navigation as more workflow stages are added. */
@customElement('aerofoil-app')
export class AerofoilApp extends LitElement {
  override createRenderRoot(): this {
    return this;
  }

  override render() {
    return html`<aerofoil-start-design-screen></aerofoil-start-design-screen>`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'aerofoil-app': AerofoilApp;
  }
}
