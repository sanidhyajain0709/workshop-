# Variables banao
lane_name = 'North'
vehicle_count = 12
avg_speed = 45.5
is_emergency = False
# Print karo
print('Lane:', lane_name)
print('Vehicles:', vehicle_count)
print('Speed:', avg_speed, 'km/h')
print('Emergency:', is_emergency)
vehicle_count = 18
if vehicle_count > 20:
 print('Bahut zyada traffic — 60s green')
elif vehicle_count > 10:
 print('Thoda traffic — 30s green')
else:
 print('Kam traffic — 15s green')