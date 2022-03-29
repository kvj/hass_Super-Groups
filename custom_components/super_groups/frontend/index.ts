import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { EditorParams } from './editor';
import './editor';
import './confirm';

const tabs = [
    {
        path: "/super_groups",
        name: "Super Groups",
        icon: "hass:view-dashboard",
    }
];

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

    @state()
    private _removeItem: EditorParams | undefined = undefined;

    _columns(narrow: boolean) {
        const columns: any = {
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
                width: narrow? undefined: "300px",
                grows: narrow? true: false,
                template: (value: string, row: any) => html`
                    <a href="/config/devices/device/${row["device_id"]}">${value}</a>
                `,
            },
        };
        if (!narrow) {
            columns["members"] = {
                title: "Group Members",
                sortable: false,
                filterable: false,
                direction: "asc",
                grows: true,
                template: (value: any[], row: any) => {
                    const list = value.map((e) => e.title);
                    let suffix = "";
                    if (["sensor", "number"].includes(row["domain"])) suffix = ` (${row["stat"]})`;
                    return html`${list.join(", ")}${suffix}`
                },
            };
        }
        columns["edit"] = {
            title: "",
            filterable: false,
            grows: false,
            template: (value: string, row: EditorParams) => {
                const _action = () => {
                    this._edit(row)
                };
                return html`
                    <mwc-button
                        @click=${_action}
                    >
                        Edit
                    </mwc-button>
                `;
            }
        };
        columns["remove"] = {
            title: "",
            filterable: false,
            grows: false,
            template: (value: string, row: EditorParams) => {
                const _action = () => {
                    this._removeItem = row;
                };
                return html`
                    <mwc-button
                        @click=${_action}
                    >
                        Remove
                    </mwc-button>
                `;
            }
        };
        return columns;
    }

    async _remove(event: any) {
        console.log('_remove', event);
        const row = event.detail.value;
        await this.hass.connection.sendMessagePromise({
            type: "super_groups/remove_entry",
            entry_id: row.id,
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

    _edit(item: EditorParams) {
        // console.log("_edit:", item.detail.id);
        const _item: any = this._items.find((_item: any) => _item.id == item.id);
        this._editorParams = {
            id: _item.id,
            title: _item.title,
            allOn: _item.all_on,
            domain: _item.domain,
            entry: _item.entry,
            stat: _item.stat,
        };
    }

    _add() {
        this._editorParams = {
            id: undefined,
            title: "New Group",
            allOn: false,
            domain: "light",
            stat: "avg",
            entry: {
                entity_id: [],
                device_id: [],
                area_id: [],
            },
        };
    }

    async _save(event: any) {
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
            stat: entry.stat,
            all_on: entry.allOn,
            items: entry.entry
        };
        // console.log("On save:", event, data, entry);
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
            id="id"
            hasFab
        >
            <ha-fab
                slot="fab"
                label="Add new"
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
        <sg-confirmation-dialog
            .data=${this._removeItem}
            @yes=${this._remove}
            text="Really remove?"
        >
        </sg-confirmation-dialog>
        `;
    }
}
