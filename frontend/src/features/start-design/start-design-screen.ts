import { LitElement, css, html, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import { createBlankDesign, importMesh, type DesignBrief } from '../../api/design-briefs.js';
import '../../components/choice-card.js';
import { tokens } from '../../styles/tokens.js';

/** The first screen deliberately presents only the two durable ways to begin a design. */
@customElement('aerofoil-start-design-screen')
export class StartDesignScreen extends LitElement {
  @state() private selectedMesh: File | null = null;
  @state() private pending = false;
  @state() private createdDesign: DesignBrief | null = null;
  @state() private errorMessage: string | null = null;

  // Arrow functions preserve this screen as the native click event owner across the card's shadow boundary.
  private readonly handleBlankChoice = (): void => {
    void this.createBlank();
  };

  private readonly handleMeshChoice = (): void => {
    void this.createFromMesh();
  };

  private async createBlank(): Promise<void> {
    await this.create(() => createBlankDesign());
  }

  private async createFromMesh(): Promise<void> {
    if (this.selectedMesh === null) {
      this.errorMessage = 'Choose an OBJ or STL mesh before importing.';
      return;
    }
    await this.create(() => importMesh(this.selectedMesh as File));
  }

  private async create(action: () => Promise<DesignBrief>): Promise<void> {
    this.pending = true;
    this.errorMessage = null;
    try {
      this.createdDesign = await action();
    } catch (error: unknown) {
      this.errorMessage = error instanceof Error ? error.message : 'The design could not be created. Try again.';
    } finally {
      this.pending = false;
    }
  }

  private selectMesh(event: Event): void {
    const input = event.currentTarget as HTMLInputElement;
    this.selectedMesh = input.files?.item(0) ?? null;
    this.errorMessage = null;
  }

  override render() {
    if (this.createdDesign !== null) {
      const origin = this.createdDesign.origin === 'blank' ? 'blank design' : this.createdDesign.mesh_filename;
      return html`
        <main class="confirmation" aria-labelledby="confirmation-heading">
          <p class="eyebrow">Design created</p>
          <h1 id="confirmation-heading">${origin} is ready.</h1>
          <p>The next screen will describe the aircraft mission and operating envelope.</p>
        </main>
      `;
    }

    return html`
      <main aria-labelledby="page-heading">
        <header>
          <p class="eyebrow">Aerofoil Tester</p>
          <h1 id="page-heading">Start a wing design.</h1>
          <p class="intro">Begin with a clean parametric model or bring an existing mesh for later inspection.</p>
        </header>

        <section class="choices" aria-label="Ways to start a design">
          <aerofoil-choice-card
            heading="Start from scratch"
            detail="Create a blank design brief. You will define the aircraft mission before choosing wing geometry."
            ?disabled=${this.pending}
            @click=${this.handleBlankChoice}
          >
            <span slot="action">Create blank design</span>
          </aerofoil-choice-card>

          <div class="import-choice">
            <aerofoil-choice-card
              heading="Import a mesh"
              detail="Add an existing OBJ or STL mesh. Importing stores the source; it does not yet validate the mesh."
              ?disabled=${this.pending}
              @click=${this.handleMeshChoice}
            >
              <span slot="action">Import selected mesh</span>
            </aerofoil-choice-card>
            <label for="mesh">Mesh file</label>
            <input id="mesh" type="file" accept=".obj,.stl" @change=${this.selectMesh} ?disabled=${this.pending} />
            <p class="file-status">${this.selectedMesh?.name ?? 'No file selected'}</p>
          </div>
        </section>

        ${this.errorMessage === null ? nothing : html`<p class="error" role="alert">${this.errorMessage}</p>`}
      </main>
    `;
  }

  static override styles = [
    tokens,
    css`
      :host {
        display: block;
        min-height: 100vh;
        background: var(--canvas);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      }

      main {
        width: min(100% - 3rem, 68rem);
        margin: 0 auto;
        padding: 12vh 0 var(--space-6);
      }

      header {
        max-width: 42rem;
      }

      .eyebrow {
        margin: 0 0 var(--space-2);
        color: var(--action);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      h1 {
        margin: 0;
        font-size: clamp(2rem, 5vw, 3.5rem);
        letter-spacing: -0.045em;
        line-height: 1.05;
      }

      .intro,
      .confirmation > p:not(.eyebrow) {
        max-width: 39rem;
        margin: var(--space-3) 0 0;
        color: var(--muted-ink);
        font-size: 1.05rem;
        line-height: 1.6;
      }

      .choices {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: var(--space-3);
        margin-top: var(--space-5);
      }

      .import-choice label {
        display: block;
        margin-top: var(--space-3);
        font-size: 0.875rem;
        font-weight: 650;
      }

      input {
        width: 100%;
        margin-top: var(--space-1);
        color: var(--muted-ink);
      }

      .file-status {
        margin: var(--space-1) 0 0;
        color: var(--muted-ink);
        font-size: 0.875rem;
      }

      .error {
        margin: var(--space-4) 0 0;
        color: var(--error);
      }

      .confirmation {
        max-width: 42rem;
      }

      @media (max-width: 44rem) {
        main {
          width: min(100% - 2rem, 68rem);
          padding-top: var(--space-6);
        }

        .choices {
          grid-template-columns: 1fr;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        * {
          transition: none !important;
        }
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    'aerofoil-start-design-screen': StartDesignScreen;
  }
}
