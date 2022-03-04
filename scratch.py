from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as md

#a generator that gives time between start and end times with delta intervals
def deltatime(start, end, delta):
    current = start
    while current < end:
        yield current
        current += delta

# two random consecutive dates [date1, date2]
dates = [('01/02/1991', '02/02/1991')] #, '01/03/1991', '01/04/1991']

# generate the list for each date between 00:00 on date1 to 00:00 on date2 with 60 minute intervals
datetimes=[]
for start, end in dates:
    startime=datetime.combine(datetime.strptime(start, "%d/%m/%Y"), datetime.strptime('0:00:00',"%H:%M:%S").time())
    endtime=datetime.combine(datetime.strptime(end, "%d/%m/%Y"), datetime.strptime('01:00:00',"%H:%M:%S").time())
    datetimes.append([j for j in deltatime(startime,endtime, timedelta(minutes=60))])

# #flatten datetimes list
datetimes=[datetime for day in datetimes for datetime in day]
xs = datetimes
# ys = range(len(xs))

# # plot
# fig, ax = plt.subplots(1, 1)
# ax.plot(xs, ys,'ok')

# # From the SO:https://stackoverflow.com/questions/42398264/matplotlib-xticks-every-15-minutes-starting-on-the-hour
# ## Set time format and the interval of ticks (every 240 minutes)
# xformatter = md.DateFormatter('%H:%M')
# xlocator = md.MinuteLocator(interval = 240)

# ## Set xtick labels to appear every 240 minutes
# ax.xaxis.set_major_locator(xlocator)

# ## Format xtick labels as HH:MM
# plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
# plt.show()