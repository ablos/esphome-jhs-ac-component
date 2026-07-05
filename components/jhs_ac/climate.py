import esphome.config_validation as cv
import esphome.codegen as cg
import esphome.automation as automation

from esphome.components import climate, uart, binary_sensor, output
from esphome.const import (
    CONF_ID,
    CONF_TRIGGER_ID,
)
from esphome.components.climate import (
    validate_climate_fan_mode,
    validate_climate_swing_mode,
    validate_climate_mode,
)

CODEOWNERS = ["@SNMetamorph"]
DEPENDENCIES = ["climate", "uart"]
AUTO_LOAD = ["binary_sensor", "output"]

CONF_PROTOCOL_VERSION = "protocol_version"
CONF_SUPPORTED_MODES = "supported_modes"
CONF_SUPPORTED_FAN_MODES = "supported_fan_modes"
CONF_SUPPORTED_SWING_MODES = "supported_swing_modes"

CONF_ON_INTERACTION = "on_interaction"
CONF_WATER_TANK_STATUS = "water_tank_status"
ICON_WATER_TANK_STATUS = "mdi:water-alert"

CONF_LED_DISPLAY = "led_display"
CONF_LED_POWER_GROUP = "led_power_group"
CONF_LED_MODE_GROUP = "led_mode_group"
CONF_LED_WAKE_DURATION = "led_wake_duration"

jhs_ac_ns = cg.esphome_ns.namespace("jhs_ac")
JhsAirConditioner = jhs_ac_ns.class_(
    "JhsAirConditioner", climate.Climate, uart.UARTDevice, cg.Component
)
JhsAcInteractionTrigger = jhs_ac_ns.class_(
    "JhsAcInteractionTrigger", automation.Trigger.template()
)

CONFIG_SCHEMA = cv.All(
    climate.climate_schema(JhsAirConditioner).extend(
        {
            cv.Required(CONF_PROTOCOL_VERSION): cv.int_range(1, 2),
            cv.Required(CONF_SUPPORTED_MODES): cv.ensure_list(validate_climate_mode),
            cv.Required(CONF_SUPPORTED_FAN_MODES): cv.ensure_list(validate_climate_fan_mode),
            cv.Optional(CONF_SUPPORTED_SWING_MODES): cv.ensure_list(validate_climate_swing_mode),
            cv.Optional(CONF_ON_INTERACTION): automation.validate_automation({
                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(JhsAcInteractionTrigger),
            }),
            cv.Optional(CONF_WATER_TANK_STATUS): binary_sensor.binary_sensor_schema(
                icon=ICON_WATER_TANK_STATUS,
            ),
            cv.Optional(CONF_LED_DISPLAY): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_LED_POWER_GROUP): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_LED_MODE_GROUP): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_LED_WAKE_DURATION, default="5s"): cv.positive_time_period_milliseconds,
        }
    )
    .extend(uart.UART_DEVICE_SCHEMA),
)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await climate.register_climate(var, config)
    await uart.register_uart_device(var, config)

    cg.add_define("JHS_AC_PROTOCOL_VERSION", config[CONF_PROTOCOL_VERSION])

    if CONF_SUPPORTED_MODES in config:
        for mode in config[CONF_SUPPORTED_MODES]:
            cg.add(var.add_supported_mode(mode))

    if CONF_SUPPORTED_FAN_MODES in config:
        for fan_mode in config[CONF_SUPPORTED_FAN_MODES]:
            cg.add(var.add_supported_fan_mode(fan_mode))

    if CONF_SUPPORTED_SWING_MODES in config:
        for swing_mode in config[CONF_SUPPORTED_SWING_MODES]:
            cg.add(var.add_supported_swing_mode(swing_mode))

    for conf in config.get(CONF_ON_INTERACTION, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID], var)
        await automation.build_automation(trigger, [], conf)

    if CONF_WATER_TANK_STATUS in config:
        conf = config[CONF_WATER_TANK_STATUS]
        sens = await binary_sensor.new_binary_sensor(conf)
        cg.add(var.set_water_tank_sensor(sens))

    cg.add(var.set_led_wake_duration(config[CONF_LED_WAKE_DURATION]))

    if CONF_LED_DISPLAY in config:
        led = await cg.get_variable(config[CONF_LED_DISPLAY])
        cg.add(var.set_led_display(led))
    if CONF_LED_POWER_GROUP in config:
        led = await cg.get_variable(config[CONF_LED_POWER_GROUP])
        cg.add(var.set_led_power_group(led))
    if CONF_LED_MODE_GROUP in config:
        led = await cg.get_variable(config[CONF_LED_MODE_GROUP])
        cg.add(var.set_led_mode_group(led))
