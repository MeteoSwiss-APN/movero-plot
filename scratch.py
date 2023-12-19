"This is just a test file."
# Third-party
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.autolayout"] = True

fig, ax = plt.subplots(1, 1)
y = [np.nan, 1.0873, 1.29964, 1.32833, 1.34151]
x_ticks = ["01-06", "07-12", "13-18", "19-24", "25-30"]
x_int = [idx for idx, _ in enumerate(y)]
print(x_int)
x_int_new = list(range(len(y)))
print(x_int_new)
x_new = list(range(len(x_ticks)))
print(x_new)

ax.plot(x_int, y, "o-", color="lightgrey", label="No mask")
ax.set_xticks(range(len(x_ticks)), x_ticks)
# plt.plot(x2*0.4, y2, 'o-', label='Points removed')
# plt.plot(x*0.7, y3, 'o-', label='Masked values')
# plt.plot(x*1.0, y4, 'o-', label='NaN values')
ax.legend()
plt.savefig("asdf.png")


# x = [0,1,2,3,4,5,6,7,8]
# y = ['Stairs',np.nan, 'Sitting', np.nan, 'Stairs',
# 'Falling','Falling','Standing',np.nan]  # noqa: E501
# y_ticks = ['Stairs', 'Sitting', 'Falling', 'Standing']
# y_int = [np.nan if elem is np.nan else y_ticks.index(elem) for elem in y]
# plt.plot(x, y_int, '.-')
# plt.yticks(range(len(y_ticks)), y_ticks)

# plt.savefig('asdfa.png')
