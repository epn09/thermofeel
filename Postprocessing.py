import sys
import eccodes
import datetime
import numpy as np
import pandas as pd

import datetime
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade

from ThermoFeel import *

def decode_grib(fpath):
    messages = []
    i = 0
    with open(fpath, "rb") as f:
        while True:
            msg = eccodes.codes_any_new_from_file(f)
            if msg is None:
                break

            i += 1
            print("message %d ----------------------------------", i)

            md = dict()

            # decode metadata

            # loop metadata key-values
            # it = eccodes.codes_keys_iterator_new(msg, 'mars')
            # while eccodes.codes_keys_iterator_next(it):
            #     k = eccodes.codes_keys_iterator_get_name(it)
            #     v = eccodes.codes_get_string(msg, k)
            #     print("%s = %s" % (k, v))
            # eccodes.codes_keys_iterator_delete(it)

            # time_l = eccodes.codes_get_long(msg, "time")
            # time_f = eccodes.codes_get_double(msg, "time")

            time = eccodes.codes_get_long(msg, "time")
            date = eccodes.codes_get_string(msg, "date")
            step = eccodes.codes_get_double(msg, "step")

            dateobj = pd.to_datetime(date, format='%Y%m%d')

            forecast_datetime = dateobj + \
                pd.to_timedelta(60*time/100, unit='min') + \
                pd.to_timedelta(60*step, unit='min')

            md["date"] = date
            md["step"] = step
            md["time"] = time
            md["datetime"] = forecast_datetime

            # decode data
            # get the lats, lons, values
            md["lats"] = eccodes.codes_get_double_array(msg, "latitudes")
            # print(lats)
            md["lons"] = eccodes.codes_get_double_array(msg, "longitudes")
            # print(lons)
            md["values"] = eccodes.codes_get_double_array(msg, "values")
            # print(values)
            eccodes.codes_release(msg)

            messages.append(md)

    f.close()
    return messages

def plot_colour_map(lats, lons, data):
    # fig = plt.figure(figsize=(10, 5))
    # ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # date = datetime.datetime(1999, 12, 31, 12)

    # ax.set_title('Night time shading for {}'.format(date))
    # ax.stock_img()
    # ax.add_feature(Nightshade(date, alpha=0.2))
    # plt.show()
    fig = plt.figure(figsize=(10, 5))
    # ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mollweide())
    # ax = fig.add_subplot(1, 1, 1, projection=ccrs.Orthographic(90))
    # ax = fig.add_subplot(1, 1, 1, projection=ccrs.EckertIV())
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    ax.contourf(lons, lats, data,
                transform=ccrs.PlateCarree(),
                cmap='nipy_spectral')
    ax.coastlines()
    ax.set_global()
    plt.show()


def calc_cossza(message):
    
    lats = message["lats"]
    lons = message["lons"]
    assert lats.size == lons.size

    print(lats.size)

    dt = pd.to_datetime(message["datetime"], format='%Y%m%d %H:%m:%s')
    date = message["date"]
    time = message["time"]
    step = message["step"]
    cossza = []
    # c2 = []
    for i in range(len(lats)):
        v = calculate_solar_zenith_angle(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour)
        cossza.append(v)
    #     # c2.append(
    #     #     calculate_solar_zenith_angle_f(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour, base=time/100, step=step))


    latsmat = np.reshape(lats, (181, 360))
    lonsmat = np.reshape(lons, (181, 360))
    cosszam = np.reshape(cossza, (181, 360))

    plot_colour_map(latsmat, lonsmat, cosszam)

    return cossza


def calc_heatindex(values):
    output = calculate_heat_index(values[0])
    return(output)


def main():
    try:
        msgs = decode_grib(sys.argv[1])
        print(msgs)
        for m in msgs:
            cossza = calc_cossza(m)
            # print(cossza)

        # calc_heatindex(decode_singleparam(sys.argv[1]))
    except eccodes.CodesInternalError as err:
        if eccodes.VERBOSE:
            eccodes.traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(err.msg + '\n')

        return 1


if __name__ == "__main__":
    sys.exit(main())