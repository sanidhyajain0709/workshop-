lane_name = 'North'
vehicle_count = 18
signal_state = 'RED'

# if/elif — green time decide karo
if vehicle_count > 20:
    green_time = 60
elif vehicle_count > 10:
    green_time = 30
else:
    green_time = 15

print(lane_name, 'lane —', vehicle_count, 'vehicles')
print('Recommended green time:', green_time, 'seconds')

# match-case — current state batao
match signal_state:
    case 'GREEN':
        print('Signal abhi GREEN hai — gaadiyaan ja sakti hain')
    case 'RED':
        print('Signal RED hai — rukna padega')
    case 'YELLOW':
        print('Signal YELLOW — slow down karo')
    case _:
        print('Signal state unknown')