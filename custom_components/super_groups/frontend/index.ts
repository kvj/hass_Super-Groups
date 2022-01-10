import { html, css, LitElement } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { EditorParams } from './editor';
import './editor';

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
