import wetstat.csvtools as csvtools
import wetstat.models as models

dd1 = csvtools.load_csv_to_daydata(r"C:\Users\dev\PycharmProjects\wetstatServer\data\day001in13.csv")
dd2 = csvtools.load_csv_to_daydata(r"C:\Users\dev\PycharmProjects\wetstatServer\data\day002in13.csv")
dc = csvtools.DataContainer([dd1, dd2])

models.generate_plot(dc, 20)
