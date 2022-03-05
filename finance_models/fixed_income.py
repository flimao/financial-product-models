#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from typing import List
import datetime as dt
import numpy as np
import pandas as pd
from . import tools

def calc_pv(
        fv: float, 
        time: float, 
        rate: float,
    ):
        """
        calculate present value of a cashflow given future value, rate and time

        fv: float -> future value
        time: float -> time between future and present. Unit must be the same as rate (e.g. rate in % year -> time in years)
        rate: float -> rate in %.
        """

        pv = fv / (1 + rate) ** time

        return pv

def calc_rate(
    pv: float,
    fv: float,
    time: float,
):
    """
    calculate rate (in % over period) given present value, future value and time

    pv: float -> present value
    fv: float -> future value
    time: float -> time (unit must be whatever is desired for rate. If rate is desired to be in % over year, time must be in years)
    """

    # fv = pv * (1 + rate) ** time
    rate = np.exp((np.log(fv) - np.log(pv)) / time) - 1
    
    return rate

