import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export type EntryRecord = {
    entity_id: string[];
    device_id: string[];
    area_id: string[];
};

export type EditorParams = {
    id: string | undefined;
    title: string;
    allOn: boolean;
    entry: EntryRecord;
    domain: string;
    stat: string | undefined;
};

@customElement("super-groups-editor")
export class SuperGroupsEditor extends LitElement {

    @property()
    data: EditorParams | undefined = undefined;

    @property()
    hass: any

    protected willUpdate(props: Map<string | number | symbol, unknown>): void {
        if (props.has("data")) {
            this._data = this.data;
        }
    }

    @state()
    _data: EditorParams | undefined = undefined;

    _cancel() {
        this._data = undefined;
    }

    _close() {
        this.dispatchEvent(new CustomEvent('save', {
            detail: {
                ...this._data,
            }, 
            bubbles: false
        }));
        this._data = undefined;
    }

    _titleChanged(event: any) {
        this._data = {
            ...this._data,
            title: event.detail.value,
        };
    }

    _allOnChanged(event: any) {
        this._data = {
            ...this._data,
            allOn: event.detail.value,
        };
    }

    @property()
    _targetSelector : {} = {
        target: {},
    };

    _domainMap: any = {
        "light": "Light",
        "binary_sensor": "Binary Sensor",
        "switch": "Switch",
        "climate": "Climate",
        "cover": "Cover",
        "sensor": "Sensor",
        "number": "Number",
    };

    _statFnMap: any = {
        "avg": "Avg",
        "min": "Min",
        "max": "Max",
        "sum": "Sum",
    };

    @property()
    _allOnSelector : {} = {
        boolean: {},
    };

    _onDomainChanged(event: any) {
        this._data = {
            ...this._data,
            domain: Object.entries(this._domainMap).find((e) => e[1] == event.detail.value)[0],
        };
    };

    _asArray(value: string | string[] | undefined) {
        const res = value || [];
        return Array.isArray(res)? res: [res];
    }

    _onEntryChanged(event: any) {
        const value = event.detail.value as EntryRecord;
        // console.log("_entryChanged:", this._data.entry, value);
        this._data = {
            ...this._data,
            entry: {
                area_id: this._asArray(value.area_id),
                device_id: this._asArray(value.device_id),
                entity_id: this._asArray(value.entity_id),
            },
        };
    };

    protected render() {
        if (!this._data) return html``;
        const _titleInvalid = !this._data.title.trim();
        let titleRow = html``;
        let dialogTitle = this._data.title;
        let domainSelector = html``;
        let statFnSelector = html``;
        if (!this._data.id) {
            titleRow = html`
                <paper-input
                    .value=${this._data.title}
                    @value-changed=${this._titleChanged}
                    label="Group name"
                    .invalid=${_titleInvalid}
                    .errorMessage="Mandatory field"
                    dialogInitialFocus
                >
                </paper-input>
            `;
            dialogTitle = 'New Super Group';
            const _domainSelector = {
                select: {
                    options: Object.values(this._domainMap),
                },
            };
            domainSelector = html`
                <ha-selector
                    label="Group type"
                    .hass=${this.hass}
                    .selector=${_domainSelector}
                    .value=${this._domainMap[this._data.domain]}
                    @value-changed=${this._onDomainChanged}
                >
                </ha-selector>    
            `;
            if (["sensor", "number"].includes(this._data.domain)) {
                const _statSelector = {
                    select: {
                        options: Object.values(this._statFnMap),
                    }
                };
                const _onStatSelected = (evt: any) => {
                    this._data = {
                        ...this._data,
                        stat: Object.entries(this._statFnMap).find((e) => e[1] == evt.detail.value)[0],
                    };            
                };
                statFnSelector = html`
                    <ha-selector
                        label="Statistic type"
                        .hass=${this.hass}
                        .selector=${_statSelector}
                        .value=${this._statFnMap[this._data.stat]}
                        @value-changed=${_onStatSelected}
                    >
                    </ha-selector>    
                `;
            }
        }
        return html`
        <ha-dialog 
            scrimClickAction
            escapeKeyAction
            .heading=${dialogTitle}
            open
        >
            <div>
                <div class="form">
                    <div>
                        ${titleRow}
                    </div>
                    <div>
                        ${domainSelector}
                    </div>
                    <div>
                        ${statFnSelector}
                    </div>
                    <div>
                        <ha-selector
                            label="Turn ON if all grouped entities are ON"
                            .hass=${this.hass}
                            .selector=${this._allOnSelector}
                            .value=${this._data.allOn}
                            @value-changed=${this._allOnChanged}
                            >
                        </ha-selector-target>
                    </div>
                    <div>
                        <ha-selector
                            label="Group entry"
                            .hass=${this.hass}
                            .selector=${this._targetSelector}
                            .value=${this._data.entry}
                            @value-changed=${this._onEntryChanged}
                        >
                        </ha-selector-target>
                    </div>
                </div>
            </div>
            <mwc-button
                @click=${this._close}
                slot="primaryAction"
            >
                Save
            </mwc-button>
            <mwc-button
                @click=${this._cancel}
                slot="secondaryAction"
            >
                Cancel
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
            .bottomRow {
                text-align: center;
            }
            .row {
                display: flex;
                align-items: center;
            }
        `;
    }
}