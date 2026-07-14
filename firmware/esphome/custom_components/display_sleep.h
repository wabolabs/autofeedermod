#pragma once
#include "esphome.h"
#include "driver/gpio.h"

class DisplaySleepComponent : public Component {
 public:
  DisplaySleepComponent(uint8_t dc_pin, uint8_t cs_pin, uint8_t clk_pin, uint8_t mosi_pin)
      : dc_(dc_pin), cs_(cs_pin), clk_(clk_pin), mosi_(mosi_pin) {}

  void setup() override {
    ESP_LOGI("display_sleep", "DisplaySleepComponent ready");
  }

  void send_cmd(uint8_t cmd) {
    gpio_set_level((gpio_num_t)dc_, 0);
    gpio_set_level((gpio_num_t)cs_, 0);
    for (int i = 7; i >= 0; i--) {
      gpio_set_level((gpio_num_t)clk_, 0);
      gpio_set_level((gpio_num_t)mosi_, (cmd >> i) & 1);
      gpio_set_level((gpio_num_t)clk_, 1);
    }
    gpio_set_level((gpio_num_t)cs_, 1);
    gpio_set_level((gpio_num_t)dc_, 1);
  }

  void sleep() {
    gpio_set_direction((gpio_num_t)dc_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)cs_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)clk_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)mosi_, GPIO_MODE_OUTPUT);
    gpio_set_level((gpio_num_t)dc_, 1);
    gpio_set_level((gpio_num_t)cs_, 1);
    gpio_set_level((gpio_num_t)clk_, 0);
    gpio_set_level((gpio_num_t)mosi_, 0);
    send_cmd(0xAE);
    send_cmd(0x2E);
    ESP_LOGI("display_sleep", "OLED sleep");
  }

  void wake() {
    gpio_set_direction((gpio_num_t)dc_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)cs_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)clk_, GPIO_MODE_OUTPUT);
    gpio_set_direction((gpio_num_t)mosi_, GPIO_MODE_OUTPUT);
    gpio_set_level((gpio_num_t)dc_, 1);
    gpio_set_level((gpio_num_t)cs_, 1);
    gpio_set_level((gpio_num_t)clk_, 0);
    gpio_set_level((gpio_num_t)mosi_, 0);
    send_cmd(0x2D);
    send_cmd(0x01);
    send_cmd(0xAF);
    ESP_LOGI("display_sleep", "OLED wake");
  }

 private:
  uint8_t dc_, cs_, clk_, mosi_;
};
