import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

const tabs = [
    {
        path: "/super_groups",
        name: "Super Groups",
        icon: "hass:view-dashboard",
    }
];

type EntryRecord = {
    entity_id: string[];
    device_id: string[];
    area_id: string[];
};

@customElement("super-groups-panel")
export class SuperGroupsPanel extends LitElement {

    @property()
    hass: any

    @property()
    narrow: boolean

    @property()
    route: object

    @property()
    panel: object

    @state()
    private _items: object[] | undefined = undefined;

    @state()
    _editorParams: EditorParams | undefined = undefined;

    _columns(narrow: boolean) {
        return {
            id: {
                hidden: true,
            },
            icon: {
                title: "",
                type: "icon",
                template: (icon: string) =>
                    icon
                        ? html` <ha-icon slot="item-icon" .icon=${icon}></ha-icon> `
                        : html``,
            },
            title: {
                title: "Name",
                sortable: true,
                filterable: true,
                direction: "asc",
                grows: true,
                template: (value: string) => html`${value}`,
            },
            remove: {
                title: "Remove",
                filterable: false,
                grows: false,
                template: (value: string, row?: any) => {
                    const _action = () => {
                        this._remove(row.id);
                    };
                    return html`
                        <mwc-button
                            @click=${_action}
                        >
                            Remove
                        </mwc-button>
                    `;
                }
            }
        };
    }

    async _remove(id: string) {
        await this.hass.connection.sendMessagePromise({
            type: "super_groups/remove_entry",
            entry_id: id,
        });
        this._load();
    }

    async _load() {
        const resp = await this.hass.connection.sendMessagePromise({
            type: "super_groups/get_entries"
        });
        // console.log("All items:", resp);
        this._items = resp.items;
    }

    _getItems(): object[] {
        if (this._items) {
            return this._items;
        }
        this._load();
        return [];
    }

    _edit(item: any) {
        // console.log("_edit:", item.detail.id);
        const _item: any = this._items.find((_item: any) => _item.id == item.detail.id);
        this._editorParams = {
            id: _item.id,
            title: _item.title,
            allOn: _item.all_on,
            domain: _item.domain,
            entry: _item.entry,
        };
    }

    _add() {
        this._editorParams = {
            id: undefined,
            title: "New Group",
            allOn: false,
            domain: "light",
            entry: {
                entity_id: [],
                device_id: [],
                area_id: [],
            },
        };
    }

    async _save(event: any) {
        // console.log("On save:", event);
        const entry = event.detail;
        const data = entry.id? {
            type: "super_groups/update_entry",
            entry_id: entry.id,
            all_on: entry.allOn,
            items: entry.entry
        } : {
            type: "super_groups/add_entry",
            title: entry.title,
            domain: entry.domain,
            all_on: entry.allOn,
            items: entry.entry
        };
        const resp = await this.hass.connection.sendMessagePromise(data);
        // console.log("_save result:", resp);
        this._load();
    }

    render() {
        // console.log("Panel: ", this.hass, this._editorParams);
        return html`
        <hass-tabs-subpage-data-table
            .hass=${this.hass}
            .narrow=${this.narrow}
            back-path="/config"
            .route=${this.route}
            .tabs=${tabs}
            .columns=${this._columns(this.narrow)}
            .data=${this._getItems()}
            @row-click=${this._edit}
            id="id"
            hasFab
            clickable
        >
            <ha-fab
                slot="fab"
                label="Add new group"
                extended
                @click=${this._add}
            >
            </ha-fab>
        </hass-tabs-subpage-data-table>
        <super-groups-editor 
            .data=${this._editorParams}
            .hass=${this.hass}
            @save=${this._save}
        >
        </super-groups-editor>
        `;
    }
}

type EditorParams = {
    id: string | undefined;
    title: string;
    allOn: boolean;
    entry: EntryRecord;
    domain: string;
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
    };

    @property()
    _domainSelector : {} = {
        select: {
            options: ["Light", "Binary Sensor", "Switch"],
        },
    };

    @property()
    _allOnSelector : {} = {
        boolean: {},
    };

    _onDomainChanged(event: any) {
        for (const [key, value] of Object.entries(this._domainMap)) {
            if (value == event.detail.value) {
                this._data = {
                    ...this._data,
                    domain: key
                };
            }
        }
    };

    _onEntryChanged(event: any) {
        const value = event.detail.value as EntryRecord;
        this._data = {
            ...this._data,
            entry: value,
        };
    };

    protected render() {
        if (!this._data) return html``;
        const _titleInvalid = !this._data.title.trim();
        let titleRow = html``;
        let dialogTitle = this._data.title;
        let domainSelector = html``;
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
            domainSelector = html`
                <ha-selector
                    label="Group type"
                    .hass=${this.hass}
                    .selector=${this._domainSelector}
                    .value=${this._domainMap[this._data.domain]}
                    @value-changed=${this._onDomainChanged}
                >
                </ha-selector>    
            `;
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