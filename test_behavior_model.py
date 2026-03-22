from behavior_auth import train_admin_model, verify_admin_behavior

registration_samples = [
    {
        "hold_times": [120, 130, 110, 125, 118],
        "flight_times": [80, 75, 78, 82],
        "total_time": 1450,
        "backspace_count": 0,
        "key_count": 5
    },
    {
        "hold_times": [122, 128, 112, 123, 120],
        "flight_times": [79, 74, 80, 81],
        "total_time": 1440,
        "backspace_count": 0,
        "key_count": 5
    },
    {
        "hold_times": [119, 131, 111, 124, 117],
        "flight_times": [81, 76, 79, 83],
        "total_time": 1465,
        "backspace_count": 1,
        "key_count": 5
    },
    {
        "hold_times": [121, 129, 113, 126, 119],
        "flight_times": [82, 73, 77, 84],
        "total_time": 1435,
        "backspace_count": 0,
        "key_count": 5
    },
    {
        "hold_times": [118, 132, 109, 127, 121],
        "flight_times": [78, 77, 81, 80],
        "total_time": 1470,
        "backspace_count": 0,
        "key_count": 5
    }
]

train_admin_model("admin", registration_samples)

login_sample = {
    "hold_times": [121, 129, 112, 124, 120],
    "flight_times": [80, 75, 79, 82],
    "total_time": 1455,
    "backspace_count": 0,
    "key_count": 5
}

result, message = verify_admin_behavior("admin", login_sample)
print(result, message)