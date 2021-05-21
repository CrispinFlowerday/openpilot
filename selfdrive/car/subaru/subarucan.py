import copy
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

def create_steering_status(packer, apply_steer, frame, steer_step):
  return packer.make_can_msg("ES_LKAS_State", 0, {})

def create_es_distance(packer, es_distance_msg, pcm_cancel_cmd):

  values = copy.copy(es_distance_msg)
  if pcm_cancel_cmd:
    values["Cruise_Cancel"] = 1

  return packer.make_can_msg("ES_Distance", 0, values)

def create_es_lkas(packer, es_lkas_msg, visual_alert, left_line, right_line, enabled):

  values = copy.copy(es_lkas_msg)
  if visual_alert == VisualAlert.steerRequired:
    values["Keep_Hands_On_Wheel"] = 1

  if values["LKAS_Alert"] == 0:
    if visual_alert == VisualAlert.ldwLeft:
      values["LKAS_Alert"] = 12

    if visual_alert == VisualAlert.ldwRight:
      values["LKAS_Alert"] = 11

  # Test some values
  values["LKAS_ACTIVE"] = os.path.exists("/tmp/lkas_active") ? 1 : 0 # Hypothesis, disable stock
  values["LKAS_ENABLE_3"] = os.path.exists("/tmp/lkas_enable_3") ? 1 : 0  # Hypothesis, enable display of left line
  values["LKAS_ENABLE_2"] = os.path.exists("/tmp/lkas_enable_2") ? 1 : 0  # Hypothesis, enable display of right line
  if os.path.exists("/tmp/lkas_signal2_1"): # 1 = white LKAS, 2 = green LKAS
    values["Signal2"] = 1 
  elif os.path.exists("/tmp/lkas_signal2_2"):
    values["Signal2"] = 2 
  else:
    values["Signal2"] = 0

  values["LKAS_Left_Line_Visible"] = int(os.path.exists("/tmp/lkas_left_visible"))
  values["LKAS_Right_Line_Visible"] = int(os.path.exists("/tmp/lkas_right_visible"))

  values["LKAS_Left_Line_Light_Blink"] = int(os.path.exists("/tmp/lkas_left_blink"))
  values["LKAS_Right_Line_Light_Blink"] = int(os.path.exists("/tmp/lkas_right_blink"))

  values["LKAS_Left_Line_Green"] = int(os.path.exists("/tmp/lkas_left_green"))
  values["LKAS_Right_Line_Green"] = int(os.path.exists("/tmp/lkas_right_green"))
  
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
