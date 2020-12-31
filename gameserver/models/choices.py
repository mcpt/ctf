import pytz

# Create your models here.

organization_request_status_choices = [
    ("p", "Pending"),
    ("a", "Approved"),
    ("r", "Rejected"),
]

timezone_choices = [(i, i) for i in pytz.all_timezones]
timezone_choices.sort(key=lambda x:x[0])
