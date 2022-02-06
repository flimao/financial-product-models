#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports

# pip install git+ssh://git@github.com:flimao/financial-product-models.git

import datetime as dt
import numpy as np
import pandas as pd
from finance_models.br_sovereign_debt import NTNF
from finance_models import tools

#%%
# test
x = NTNF()

holidays = tools.get_holidays_anbima()
# %%
