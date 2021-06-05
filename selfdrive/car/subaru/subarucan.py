import copy
import os
from cereal import car

VisualAlert = car.CarControl.HUDControl.VisualAlert

def create_steering_control(packer, apply_steer, frame, steer_step):

  idx = (frame / steer_step) % 16

  values = {
    "Counter": idx,
    "LKAS_Output": apply_steer,
    "LKAS_Request": 1 if apply_steer != 0 else 0,
    "SET_1": 1
  }

  return packer.make_can_msg("ES_LKAS", 0, values)

def create_es_distance(packer, es_distance_msg, pcm_cancel_cmd):

  values = copy.copy(es_distance_msg)
  if pcm_cancel_cmd:
    values["Cruise_Cancel"] = 1

  return packer.make_can_msg("ES_Distance", 0, values)

def create_es_lkas(packer, es_lkas_msg, enabled, visual_alert, left_line, right_line, left_lane_depart, right_lane_depart):

  values = copy.copy(es_lkas_msg)

  # If OP is engaged, then ignore stock LKAS alerts
  if enabled:
    if values["Keep_Hands_On_Wheel"] == 1:
      values["Keep_Hands_On_Wheel"] = 0

    if values["LKAS_Alert"] in [ 27 ]:
      values["LKAS_Alert"] = 0

  # Always ignore stock LDW alerts
  if values["LKAS_Alert"] in [ 11, 12 ]:
    values["LKAS_Alert"] = 0

  # Show OP alerts
  if visual_alert == VisualAlert.steerRequired:
    values["Keep_Hands_On_Wheel"] = 1
  
  if visual_alert == VisualAlert.ldw and values["LKAS_Alert"] == 0:
    if left_lane_depart:
      values["LKAS_Alert"] = 12 # Left lane departure dash alert

    elif right_lane_depart:
      values["LKAS_Alert"] = 11 # Right lane departure dash alert


  # If we are enabled, then display LKAS correctly
  if enabled:
    # Setup dash display
    values["LKAS_ACTIVE"] = 1 # Show LKAS display
    values["LKAS_Dash_Icon"] = 2 # Green enabled icon
    values["LKAS_Left_Line_Enable"] = 1 # Allow showing left line
    values["LKAS_Right_Line_Enable"] = 1 # Allow showing right line

  # Always use OP lane lines
  values["LKAS_Left_Line_Visible"] = int(left_line)
  values["LKAS_Right_Line_Visible"] = int(right_line)
    
  # Signal2=
  # LKAS_ACTIVE=
  # LKAS_Alert=

  # LKAS_ENABLE_3=
  # LKAS_Left_Line_Light_Blink=
  # LKAS_Left_Line_Visible=
  # LKAS_Left_Line_Green=

  # 1 Obstacle detechted - continuous tone
  # 2 Obstacle detected - beeping
  # 3 Throttle management activated
  # 4 Throttle management activated - red warning
  # 5 Pre collision braking system activated - orange - continuous tone
  # 8 Traffic light ahead
  # 9 Apply brake to hold position
  # 11 Right lane depart
  # 12 Left lane depart
  # 13 Stay alert
  # 14 Vehicle ahead has moved
  # 18 red flash keey hands on steering wheel (with beep)
  # 24 beep loud
  # 25 beep medium (ACC car beep)
  # 26 de-de (cruise disengaged) ??
  # 27 de-de (LKAS disengaged) ??
  # 28 ding ding ??
  # 30 de-de de-de de-de de-de
  
  # LKAS_ENABLE_2=
  # LKAS_Right_Line_Light_Blink=
  # LKAS_Right_Line_Visible=
  # LKAS_Right_Line_Green=

  # Backward_Speed_Limit_Menu
  # Empty_Box

  if os.path.exists("/tmp/lkas_values"):
    with open("/tmp/lkas_values") as myfile:
      for line in myfile:
        name, var = line.partition("=")[::2]
        name = name.strip()
        var = var.strip()
        if len(var) > 0 and var.isdigit():
          values[name] = int(var)

  return packer.make_can_msg("ES_LKAS_State", 0, values)

def create_es_dashstatus(packer, dashstatus_msg):
  values = copy.copy(dashstatus_msg)

  # Signal1 = 1/2/3 noop
  #---
  # Signal1 == 4 Cruise off steep slope
  # Signal1 == 8 Cruise lvl1 eco
  # Signal1 == 12 Cruise lvl2 comfort
  # Signal1 == 16 Cruise off - empty text
  # Signal1 == 20 Cruise off (centered)
  # Signal1 == 24 Cruise "Unable to set"
  # Signal1 == 28 Cruise Unable to set brakes applied
  # Signal1 == 32 Eyesight not ready
  # Signal1 == 36 Cruise lvl3 standard
  # Signal1 == 40 Cruise lvl4 dynamic
  # Signal1 == 44 Cruise "Unable to set Steep Slope"
  # Signal1 == 48-60 / noop
  #----
  # Signal1 == 64 LKAS off (Sharp Curve)
  # Signal1 == 128 Keep hands on steering wheel LKAS
  # Signal1 == 192 LKAS off
  # Signal1 == 256 LKAS off speed too slow
  # Signal1 == 320 LKAS off speed too fast
  # Signal1 == 284 Noop
  #---
  
  # Test Signal2 == (2 bits)
  # Signal2 == 1 Eyesight disabled, bad visibility
  # Signal2 == 2 Eyesight disabled, check manual

  # Signal6 Show Car (0/1)
  
  if os.path.exists("/tmp/es_dashstatus"):
    with open("/tmp/es_dashstatus") as myfile:
      for line in myfile:
        name, var = line.partition("=")[::2]
        name = name.strip()
        var = var.strip()
        if len(var) > 0 and var.isdigit():
          values[name] = int(var)

  return packer.make_can_msg("ES_DashStatus", 0, values)
  

def create_throttle(packer, throttle_msg, throttle_cmd):

  values = copy.copy(throttle_msg)
  if throttle_cmd:
    values["Throttle_Pedal"] = 5

  return packer.make_can_msg("Throttle", 2, values)

def create_brake_pedal(packer, brake_pedal_msg, speed_cmd):

   values = copy.copy(brake_pedal_msg)
   if speed_cmd:
     values["Speed"] = 3

   return packer.make_can_msg("Brake_Pedal", 2, values)  

# *** Subaru Pre-global ***

def subaru_preglobal_checksum(packer, values, addr):
  dat = packer.make_can_msg(addr, 0, values)[2]
  return (sum(dat[:7])) % 256

def create_preglobal_steering_control(packer, apply_steer, frame, steer_step):

  idx = (frame / steer_step) % 8

  values = {
    "Counter": idx,
    "LKAS_Command": apply_steer,
    "LKAS_Active": 1 if apply_steer != 0 else 0
  }
  values["Checksum"] = subaru_preglobal_checksum(packer, values, "ES_LKAS")

  return packer.make_can_msg("ES_LKAS", 0, values)

def create_es_throttle_control(packer, fake_button, es_accel_msg):

  values = copy.copy(es_accel_msg)
  values["Cruise_Button"] = fake_button

  values["Checksum"] = subaru_preglobal_checksum(packer, values, "ES_CruiseThrottle")

  return packer.make_can_msg("ES_CruiseThrottle", 0, values)

def create_preglobal_throttle(packer, throttle_msg, throttle_cmd):

  values = copy.copy(throttle_msg)
  if throttle_cmd:
    values["Throttle_Pedal"] = 5

  values["Checksum"] = subaru_preglobal_checksum(packer, values, "Throttle")

  return packer.make_can_msg("Throttle", 2, values)
