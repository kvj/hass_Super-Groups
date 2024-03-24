DOMAIN = "super_groups"
PLATFORMS = ["binary_sensor", "switch", "light", "cover"] # , "light", "switch", "climate", "cover"

CONF_ENTITIES = "entities"
CONF_INVERT = "invert"
CONF_TYPE = "type_"
CONF_TOGGLE = "toggle"
CONF_TYPES = [{
    "value": "binary_sensor",
    "label": "Binary Sensor",
}, {
    "value": "switch",
    "label": "Switch",
}, {
    "value": "light",
    "label": "Light",
}, {
    "value": "climate",
    "label": "Climate",
}, {
    "value": "cover",
    "label": "Cover",
}]