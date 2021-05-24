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

def create_es_lkas(packer, es_lkas_msg, visual_alert, left_line, right_line, enabled):

  if !enabled:
    return es_lkas_msg

  values = copy.copy(es_lkas_msg)

  # Clear out LKAS warnings (driver monitoring from stock)
  if values["Keep_Hands_On_Wheel"] == 1:
    values["Keep_Hands_On_Wheel"] = 0

  # Clear LKAS disabled dash alert (from stock)
  if values["LKAS_Alert"] in [ 27 ]:
    values["LKAS_Alert"] = 0

  # Setup dash display
  values["LKAS_ACTIVE"] = 1 # Show correct display
  values["LKAS_Dash_Icon"] = 2 # Green enabled icon
  values["LKAS_Left_Line_Enable"] = 1 # Allow showing left line
  values["LKAS_Right_Line_Enable"] = 1 # Allow showing right line

  # Show correct Left/Right display
  values["LKAS_Left_Line_Visible"] = int(left_line)
  values["LKAS_Right_Line_Visible"] = int(right_line)

  # Show warnings as appropriate
  if visual_alert == VisualAlert.steerRequired:
    values["Keep_Hands_On_Wheel"] = 1

  if values["LKAS_Alert"] == 0:
    if visual_alert == VisualAlert.ldwLeft:
      values["LKAS_Alert"] = 12

    if visual_alert == VisualAlert.ldwRight:
      values["LKAS_Alert"] = 11


  # Signal2=
  # LKAS_ACTIVE=
  # LKAS_Alert=

  # LKAS_ENABLE_3=
  # LKAS_Left_Line_Light_Blink=
  # LKAS_Left_Line_Visible=
  # LKAS_Left_Line_Green=

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
