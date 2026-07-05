#pragma once
#include "esphome/core/component.h"
#include "esphome/components/climate/climate.h"
#include "esphome/components/uart/uart.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/output/binary_output.h"
#include "esphome/core/log.h"
#include "esphome/core/optional.h"
#include "esphome/core/automation.h"
#include "esphome/core/helpers.h"
#include "binary_output_stream.h"
#include "ac_state.h"
#include "packet_parser.h"
#include "ring_buffer.h"

namespace esphome::jhs_ac {

struct CommandPacket
{
    uint32_t length;
    uint8_t data[18];
};

class JhsAirConditioner : public climate::Climate, public uart::UARTDevice, public esphome::Component
{
public:
    JhsAirConditioner() :
        m_water_tank_sensor(nullptr),
        m_last_command_send_time(0) {};

    static constexpr const char *TAG = "jhs-ac";
    static constexpr float MIN_VALID_TEMPERATURE = 16.0f;
    static constexpr float MAX_VALID_TEMPERATURE = 31.0f;
    static constexpr float TEMPERATURE_STEP = 1.0f;
    static constexpr uint8_t PACKET_AC_STATE_CHECKSUM_LEN = 15;
    static constexpr uint32_t TX_QUEUE_PACKETS_INTERVAL_MS = 100;

    void setup() override;
    void loop() override;
    void dump_config() override;
    void control(const climate::ClimateCall &call) override;
    float get_setup_priority() const override;
    void set_water_tank_sensor(binary_sensor::BinarySensor *sensor);
    void set_led_display(output::BinaryOutput *out) { m_led_display_ = out; }
    void set_led_power_group(output::BinaryOutput *out) { m_led_power_group_ = out; }
    void set_led_mode_group(output::BinaryOutput *out) { m_led_mode_group_ = out; }
    void set_led_wake_duration(uint32_t ms) { m_led_wake_duration_ms_ = ms; }
    void add_supported_mode(climate::ClimateMode mode);
    void add_supported_fan_mode(climate::ClimateFanMode fan_mode);
    void add_supported_swing_mode(climate::ClimateSwingMode swing_mode);
    void add_on_interaction_callback(std::function<void()> &&callback) {
        m_interaction_callbacks_.add(std::move(callback));
    }

protected:
    climate::ClimateTraits traits() override;
    void read_uart_data();
    void parse_received_data();
    void send_queued_command();
    void add_packet_to_queue(const BinaryOutputStream &packet);
    void send_packet_to_ac(const uint8_t *data, uint32_t length);
    void dump_packet(const char *title, const uint8_t *data, uint32_t length);
    void dump_ac_state(const AirConditionerState &state);
    void update_ac_state(const AirConditionerState &state);
    bool validate_state_packet_checksum(const BinaryInputStream &stream, uint32_t checksum);
    void led_wake_();
    void led_check_timeout_();

    optional<AirConditionerState::Mode> get_mapped_ac_mode(climate::ClimateMode climate_mode) const;
    optional<AirConditionerState::FanSpeed> get_mapped_fan_speed(climate::ClimateFanMode fan_mode) const;
    optional<climate::ClimateFanMode> get_mapped_climate_fan_mode(AirConditionerState::FanSpeed fan_speed) const;
    const char* get_fan_speed_name(AirConditionerState::FanSpeed fan_speed) const;

private:
    AirConditionerState m_state;
    PacketParser m_parser;
    binary_sensor::BinarySensor *m_water_tank_sensor;
    output::BinaryOutput *m_led_display_{nullptr};
    output::BinaryOutput *m_led_power_group_{nullptr};
    output::BinaryOutput *m_led_mode_group_{nullptr};
    RingBuffer<uint8_t, 128> m_data_buffer;
    RingBuffer<CommandPacket, 8> m_tx_queue;
    uint32_t m_last_command_send_time;
    uint32_t m_led_wake_duration_ms_{5000};
    uint32_t m_led_wake_time_{0};
    bool m_led_active_{false};
    bool m_water_tank_full_{false};
    bool m_water_tank_state_known_{false};
    bool m_prev_water_tank_full_{false};
    climate::ClimateTraits m_traits;
    climate::ClimateModeMask m_supported_modes;
    climate::ClimateFanModeMask m_supported_fan_modes;
    climate::ClimateSwingModeMask m_supported_swing_modes;
    CallbackManager<void()> m_interaction_callbacks_;
};

class JhsAcInteractionTrigger : public Trigger<> {
public:
    explicit JhsAcInteractionTrigger(JhsAirConditioner *parent) {
        parent->add_on_interaction_callback([this]() { this->trigger(); });
    }
};

} // namespace esphome::jhs_ac
