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

def create_es_distance(packer, es_distance_msg, pcm_cancel_cmd):

  values = copy.copy(es_distance_msg)
  if pcm_cancel_cmd:
    values["Cruise_Cancel"] = 1

  return packer.make_can_msg("ES_Distance", 0, values)

def filter_stock_ldw_alerts(values):
  # Filter out stock lane departure alerts
  if values["LKAS_Alert"] in [ 11, 12 ]:
    values["LKAS_Alert"] = 0

  return values

def filter_stock_lkas_alerts(values):
  # Remove the Stock "Keep hands on wheel" alert
  if values["Keep_Hands_On_Wheel"] == 1:
    values["Keep_Hands_On_Wheel"] = 0

  # Prevent Stock sending an audible tone if it turns off LKAS
  if values["LKAS_Alert"] == 27:
    values["LKAS_Alert"] = 0

  return values

def filter_stock_lkas_dashstatus(values):
  # Prevent stock showing an LKAS disabled message
  if values["LKAS_State_Msg"] == 3:
    values["LKAS_State_Msg"] = 0

  return values

def create_es_lkas(packer, es_lkas_msg, enabled, visual_alert, left_line, right_line, left_lane_depart, right_lane_depart):
  values = copy.copy(es_lkas_msg)

  # Prevent stock showing confusing messages
  values = filter_stock_ldw_alerts(values)
  values = filter_stock_lkas_alerts(values)

  # Show OP alerts
  if visual_alert == VisualAlert.steerRequired:
    values["Keep_Hands_On_Wheel"] = 1

  # Ensure we don't overwrite potentially more important alerts from stock (e.g. FCW)
  if visual_alert == VisualAlert.ldw and values["LKAS_Alert"] == 0:
    if left_lane_depart:
      values["LKAS_Alert"] = 12 # Left lane departure dash alert

    elif right_lane_depart:
      values["LKAS_Alert"] = 11 # Right lane departure dash alert


  # Setup the LKAS dash display
  if enabled:
    values["LKAS_ACTIVE"] = 1 # Show LKAS display
    values["LKAS_Dash_Icon"] = 2 # Green enabled icon
  else:
    # By leaving LKAS_ACTIVE to the stock, it makes the button on the steering wheel toggle
    # the display, but by setting LKAS_Dash_Icon to 0 means the dash doesn't show
    # that LKAS is active (which it isn't because OP controls it)
    # values["LKAS_ACTIVE"] = 0
    values["LKAS_Dash_Icon"] = 0

  # Setup it up so the lane lines show from OP
  values["LKAS_Left_Line_Enable"] = 1
  values["LKAS_Right_Line_Enable"] = 1
  values["LKAS_Left_Line_Visible"] = int(left_line)
  values["LKAS_Right_Line_Visible"] = int(right_line)

  return packer.make_can_msg("ES_LKAS_State", 0, values)

def create_es_dashstatus(packer, dashstatus_msg):
  values = copy.copy(dashstatus_msg)

  values = filter_stock_lkas_dashstatus(values)

  return packer.make_can_msg("ES_DashStatus", 0, values)

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

def create_es_throttle_control(packer, cruise_button, es_accel_msg):

  values = copy.copy(es_accel_msg)
  values["Cruise_Button"] = cruise_button

  values["Checksum"] = subaru_preglobal_checksum(packer, values, "ES_CruiseThrottle")

  return packer.make_can_msg("ES_CruiseThrottle", 0, values)
