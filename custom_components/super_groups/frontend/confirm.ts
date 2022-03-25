import { css, html, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement("sg-confirmation-dialog")
class ConfirmationDialog extends LitElement {

    @property()
    data: any | undefined = undefined;

    @property()
    title: string;

    @property()
    text: string;

    @property()
    yesText: string;

    @property()
    noText: string;

    protected willUpdate(props: Map<string, unknown>): void {
        if (props.has("data") && this.data) {
            this._data = { // Copy
                ...this.data
            };
        }
    }

    @state()
    _data: any | undefined = undefined;

    _no() {
        this._data = undefined;
        this.dispatchEvent(new CustomEvent('no', {
            bubbles: false
        }));
    }

    _yes() {
        this._data = undefined;
        this.dispatchEvent(new CustomEvent('yes', {
            detail: {
                value: this.data,
            },
            bubbles: false
        }));
    }

    protected render() {
        if (!this._data) return html``;
        const header = html`
            <span class="header_title">${this.title || "Confirmation"}</span>
        `;
        const content = html`
            <p>${this.text}</p>
        `;
        return html`
        <ha-dialog 
            scrimClickAction
            escapeKeyAction
            .heading=${header}
            open
        >
            <div>
                ${content}
            </div>
            <mwc-button
                @click=${this._yes}
                slot="secondaryAction"
            >
                ${this.yesText || "Yes"}
            </mwc-button>
            <mwc-button
                @click=${this._no}
                slot="primaryAction"
            >
                ${this.noText || "No"}
            </mwc-button>
        </ha-dialog>
        `;
    }

    static get styles() {
        return css`
            ha-dialog {
                --mdc-dialog-heading-ink-color: var(--primary-text-color);
                --mdc-dialog-content-ink-color: var(--primary-text-color);
                --justify-action-buttons: space-between;
            }                    
            p {
                margin: 1em 0;
            }
        `;
    }
}