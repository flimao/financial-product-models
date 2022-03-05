#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
from .. import portfolio, tools, volatility as volm, derivatives
from ..derivatives import binomialtree as bt
import unittest

import warnings
warnings.filterwarnings('ignore')

M = tools.Money

class TestDerivatives(unittest.TestCase):
    def setUp(self):
        self.date_idx = pd.date_range(
            start = dt.date(2022, 1, 1),
            end = dt.date(2023, 5, 15),
            freq = 'D'
        )

        self.sec_names = [ 'S1', 'S2', 'S3' ]
        
        self.secs_values = pd.DataFrame(
            [
                [9.783857589, 10.55768482, 12.37094502],
                [11.20350055, 12.32349224, 10.01045319],
                [9.781798507, 12.54284593, 11.21947263],
                [12.32822775, 14.32465285, 16.65994343],
                [11.58502157, 15.75298169, 12.47235528],
                [13.46324976, 16.19449042, 14.20927807],
                [13.90880861, 16.6248472, 17.77740714],
                [14.48962037, 18.4719115, 15.68197697],
                [15.13524348, 18.77262148, 14.86025008],
                [14.96397751, 19.88662561, 20.41578696],
                [14.68013918, 21.22400794, 19.4077402],
                [17.73445251, 22.15347032, 14.18678256],
                [16.23967968, 22.10303061, 17.16367832],
                [17.60004512, 23.66833618, 15.61882969],
                [15.67527017, 25.40209307, 14.43342913],
                [17.66817834, 25.79931165, 20.84280978],
                [16.75759574, 27.30465841, 21.91386957],
                [19.43099231, 27.50057212, 20.61243029],
                [17.88970988, 28.25435069, 15.31228331],
                [18.91263455, 30.3533002, 19.01295279],
                [20.12167657, 30.68251328, 17.24508786],
                [21.01085858, 32.10450874, 15.08636416],
                [21.6412036, 33.10001605, 14.4814212],
                [20.7717559, 34.6627608, 20.52966721],
                [20.95399004, 34.19457809, 17.23811484],
                [22.19150678, 35.93780602, 19.77233973],
                [21.67366105, 37.73523764, 8.926478745],
                [22.8159525, 38.06538569, 19.86658971],
                [23.1950301, 38.33892242, 20.46623154],
                [23.98861585, 40.05058708, 15.68707193],
                [27.08107082, 40.54477691, 24.50144974],
                [24.61249131, 42.16764983, 13.0164211],
                [26.11771287, 42.85719028, 20.25898014],
                [27.10006536, 44.08962537, 22.12303174],
                [27.71744883, 46.15284008, 24.01220924],
                [25.38431071, 46.40252668, 24.75509565],
                [28.05781459, 46.94874942, 19.56795722],
                [29.18523009, 47.68380149, 24.7122775],
                [28.86679579, 49.79467944, 17.2582626],
                [30.11460101, 50.20271239, 20.19093597],
                [31.39602386, 50.6506032, 18.89497172],
                [32.00875358, 51.65313565, 26.22387623],
                [29.923153, 53.00595305, 16.99951411],
                [31.41609177, 53.08185423, 17.63482448],
                [32.28140441, 55.39188183, 22.91392647],
                [32.94007118, 56.42819977, 21.59549336],
                [34.21061885, 57.01145212, 18.62157035],
                [34.01661991, 58.10359672, 17.01388615],
                [34.30765779, 59.42323721, 22.18498713],
                [34.06313135, 59.73599302, 22.4838984],
                [33.53130287, 60.94547481, 19.67330108],
                [36.94240947, 62.03972547, 22.69534618],
                [34.1321698, 62.56003943, 19.44727477],
                [38.6343704, 63.23356621, 22.0222066],
                [37.85864329, 64.96534102, 20.64940533],
                [39.20756207, 64.76182963, 20.8501814],
                [36.87627922, 66.7749649, 23.59751062],
                [39.19012598, 68.02845137, 18.95032944],
                [38.68187027, 68.77111823, 21.31834614],
                [38.61869827, 70.02729845, 20.34666782],
                [40.72765121, 70.90113122, 25.52467675],
                [40.14290673, 71.42261786, 22.31795806],
                [39.8994316, 72.75047511, 18.41249608],
                [41.12435598, 73.72402534, 23.85987242],
                [42.1643064, 74.69265925, 17.43870825],
                [40.59877714, 75.94264712, 21.88389305],
                [43.48074996, 77.65496776, 20.11339922],
                [42.47275659, 78.83127533, 20.54365283],
                [43.74338404, 80.23087907, 23.06707257],
                [44.69593293, 79.90995459, 22.44600235],
                [45.6941572, 79.87872593, 20.93341942],
                [43.04094743, 80.99489447, 23.84704505],
                [46.33346936, 83.36510714, 22.55592558],
                [47.32020683, 83.7359636, 22.28402182],
                [47.77314862, 84.55845995, 22.10881805],
                [46.54935797, 86.11322183, 24.14881586],
                [48.07138977, 87.16266795, 24.7838987],
                [48.1063845, 88.42985306, 20.98191467],
                [50.21519439, 88.6633815, 22.37377468],
                [50.70023419, 89.80883036, 22.59032747],
                [50.36009659, 91.89838148, 19.4264487],
                [49.47085699, 92.68062711, 17.35619751],
                [51.20110584, 93.05046226, 26.70518535],
                [53.14715306, 94.93763554, 25.08122712],
                [53.76216807, 94.47008355, 22.87847042],
                [51.31506782, 96.21172082, 23.57307839],
                [54.46739378, 96.65471863, 21.80410833],
                [54.175627, 97.80387757, 22.35148015],
                [53.5174606, 98.56555762, 27.48017813],
                [53.80085961, 100.6380665, 22.70832654],
                [56.96362976, 100.6010785, 19.96869601],
                [54.82007894, 102.0706696, 24.67171629],
                [56.39299369, 103.4835739, 26.89916613],
                [54.80318027, 103.5325578, 23.60811003],
                [55.99964167, 104.8745375, 23.83892554],
                [55.49979997, 106.5104954, 23.41497626],
                [58.09228674, 107.9621368, 25.27727887],
                [59.02639343, 107.3917656, 23.75584178],
                [58.89767373, 109.0533704, 22.41765889],
                [59.83941664, 110.0131614, 25.93403833],
                [60.99121303, 111.2072574, 25.7671237],
                [58.98963629, 112.2981939, 26.90146575],
                [58.79536186, 113.1964746, 26.55991825],
                [61.81078971, 114.3765854, 27.53249083],
                [61.86081422, 115.6189847, 26.17455439],
                [62.28440551, 116.7000489, 23.83903362],
                [63.31765862, 117.1982541, 25.55938631],
                [65.52464095, 118.489289, 26.83587332],
                [63.9560526, 119.1868661, 24.81413923],
                [63.82267115, 121.3489613, 24.69479138],
                [65.01055803, 120.2753265, 26.28792913],
                [64.87598719, 122.3468995, 24.99039428],
                [66.68650863, 123.3484323, 27.131019],
                [66.12202783, 123.2977549, 26.21598529],
                [65.8700172, 124.2054664, 31.54048473],
                [67.916737, 127.0031651, 28.56909472],
                [66.46032837, 127.6481491, 28.5859847],
                [68.31217928, 128.4305058, 24.77210157],
                [69.05094983, 128.6519384, 30.82740622],
                [71.43601906, 129.6118312, 28.64949509],
                [71.2623721, 131.1769577, 27.18789358],
                [70.12797348, 132.8619222, 28.76273948],
                [70.59597153, 133.463977, 23.26415475],
                [69.77951345, 134.5659407, 24.97944867],
                [71.32329807, 134.4940627, 26.55336676],
                [72.50167046, 135.7022663, 28.63717631],
                [73.54454137, 136.8470554, 27.07281347],
                [74.70158815, 138.1194025, 30.3042281],
                [74.53931581, 138.3058004, 23.13710826],
                [73.44583777, 139.3579116, 29.52072292],
                [76.45092973, 140.3565014, 28.18130234],
                [74.81237748, 142.4148669, 22.79931369],
                [76.53224574, 143.4454706, 27.7882209],
                [76.70808274, 144.1036696, 29.30575001],
                [76.03447502, 145.2486419, 27.97363803],
                [78.68751764, 146.0200915, 25.5501425],
                [78.41567805, 147.1920218, 28.64440824],
                [77.44431226, 147.5745149, 26.62506534],
                [79.32492057, 148.5234602, 28.46407516],
                [79.6322003, 151.1162384, 32.00708042],
                [79.71169419, 151.4253461, 29.16544101],
                [81.35525743, 151.4427227, 29.8406175],
                [77.40541259, 153.1291486, 25.95278277],
                [81.79198741, 153.7609018, 35.43515063],
                [82.0813198, 155.0080136, 30.98131341],
                [83.26506213, 155.921791, 34.89359206],
                [83.48986252, 156.9103022, 26.92447423],
                [84.00494334, 158.6327818, 29.96416435],
                [86.75900999, 159.4528489, 30.91839141],
                [81.49833487, 160.2058825, 31.63162672],
                [83.90453867, 160.970473, 30.21647605],
                [87.07850902, 161.9656328, 28.53778686],
                [84.19828774, 163.0681357, 31.6140616],
                [87.92359805, 163.2295727, 30.62181905],
                [86.78402864, 165.804236, 35.0739255],
                [86.4001479, 166.3977632, 30.48752352],
                [88.78781949, 167.2728789, 28.12138132],
                [88.96723288, 168.6789106, 34.50310909],
                [88.72079255, 168.7494212, 32.18472545],
                [89.22756425, 169.6344852, 28.7522388],
                [89.87159067, 170.8324045, 31.55458686],
                [91.08779175, 172.771239, 31.6273586],
                [90.95320848, 172.3587668, 33.88963292],
                [90.45748181, 173.8004516, 33.37101718],
                [91.18843366, 175.9426888, 29.02029063],
                [92.19101787, 176.0965142, 31.49390982],
                [92.18156232, 177.3183015, 31.22466433],
                [94.37395532, 178.1334139, 30.50253909],
                [92.86323317, 178.8961189, 31.81750091],
                [94.9173335, 180.2870865, 24.77728583],
                [94.51576467, 181.5606722, 32.94514986],
                [94.48557296, 180.825028, 39.64206925],
                [96.21660616, 182.8730391, 33.47829687],
                [96.03311623, 184.4391428, 29.81443206],
                [97.04947916, 185.4955058, 36.70554104],
                [96.76113705, 185.7391331, 35.85085423],
                [99.2116079, 186.3680403, 38.20004134],
                [98.22737815, 187.1964487, 31.25886514],
                [98.88530392, 189.3861196, 33.52265365],
                [99.67378994, 190.4797849, 30.32297708],
                [100.2399475, 191.5738596, 32.68638495],
                [101.2034561, 191.1918369, 30.31796836],
                [101.1004871, 192.629977, 25.56823635],
                [101.4483359, 194.2050603, 33.54912679],
                [103.6956441, 195.0786845, 35.68724468],
                [101.2432877, 195.6682616, 31.33033073],
                [103.5921837, 196.7627199, 30.32688489],
                [104.634933, 197.7331962, 32.95784599],
                [105.0202257, 199.0110745, 31.99304803],
                [105.1828434, 200.6666518, 38.23356684],
                [104.6368144, 200.9407598, 33.22857157],
                [104.6373102, 201.8441226, 35.43378302],
                [105.1039275, 202.9587912, 35.70501833],
                [106.1370095, 203.7141952, 32.60971495],
                [106.6123085, 205.6077378, 30.84612054],
                [107.9480039, 205.8150542, 38.22764357],
                [107.6013823, 207.0533943, 35.73857308],
                [110.1059181, 207.5693686, 34.63846328],
                [107.7026787, 209.37353, 31.76223142],
                [109.755716, 209.8842824, 33.22001876],
                [108.8326025, 210.739036, 31.73832386],
                [108.5479657, 211.8572184, 36.83737086],
                [111.3336884, 212.431694, 33.04565869],
                [111.5862433, 214.5523379, 32.97073548],
                [113.3285469, 215.50285, 33.74325423],
                [113.0994338, 215.5695533, 40.490598],
                [112.8985685, 217.3305884, 38.58020675],
                [112.4291043, 217.496996, 31.12279046],
                [114.2665756, 218.9385738, 33.29534783],
                [115.4069763, 220.0685602, 37.37336257],
                [114.9922019, 221.7440727, 36.99702516],
                [115.9581161, 221.7526811, 36.0625217],
                [117.2414956, 223.543106, 34.01023026],
                [116.4902523, 224.5741232, 36.29625406],
                [116.9269767, 225.1522876, 39.36390636],
                [117.3192586, 226.197074, 35.93537803],
                [117.1700008, 227.2675361, 36.33336561],
                [116.9914776, 228.3109596, 34.62726554],
                [117.9545186, 228.8555436, 39.94303073],
                [119.2329546, 229.8936686, 35.371648],
                [120.9854095, 231.6602693, 35.33334237],
                [118.9837165, 232.5715945, 42.23531468],
                [119.6033546, 233.0240897, 40.46850783],
                [120.7621191, 233.7272098, 40.34459906],
                [120.381534, 234.9300641, 31.72473851],
                [122.5158997, 236.019724, 34.91252472],
                [123.2538033, 237.4145596, 41.24592131],
                [122.7873846, 238.2849708, 40.33002795],
                [122.5348867, 238.5619067, 32.08127304],
                [124.6717017, 239.6176649, 38.89264707],
                [124.4372729, 241.5815251, 41.58986934],
                [123.9927369, 242.2584202, 33.21820112],
                [124.8714307, 242.4996164, 37.86755914],
                [126.3724637, 243.5419539, 38.88649239],
                [127.5018061, 245.4896899, 37.87301578],
                [126.4321847, 245.7617917, 35.77589884],
                [129.0901454, 246.7474565, 43.53374069],
                [129.9469243, 247.967961, 38.15501162],
                [130.2651761, 250.0685537, 38.30114556],
                [129.928658, 249.4694731, 37.55073203],
                [130.0822393, 250.216482, 41.97636779],
                [131.2379133, 252.7826655, 40.3027357],
                [132.8391439, 252.4556974, 43.06897594],
                [130.8978537, 253.9536747, 42.73854876],
                [131.8945877, 254.9594466, 37.62071497],
                [132.178383, 255.279533, 38.43681685],
                [132.8276812, 256.5248278, 38.67475501],
                [132.1325823, 257.7911292, 41.34545436],
                [134.0138228, 259.6164822, 35.36939765],
                [135.188831, 259.9646426, 40.10500194],
                [135.2509259, 260.4124319, 33.1525034],
                [136.1333672, 262.0443417, 40.17005971],
                [135.104194, 262.8550398, 44.14770036],
                [135.3494339, 263.5789623, 38.86178281],
                [136.6603358, 265.000617, 41.0994532],
                [137.4635802, 265.5004155, 40.03293995],
                [138.1256787, 266.747932, 36.23533979],
                [137.6297081, 268.1754116, 49.81795958],
                [139.9924667, 269.4238103, 35.90324309],
                [138.739637, 270.2229611, 37.52956361],
                [140.5278304, 270.5166494, 41.61774893],
                [139.7392485, 271.0520869, 40.8041774],
                [142.0895177, 272.3360884, 43.33903265],
                [139.9001877, 273.9837469, 40.27679737],
                [142.4275175, 275.0663019, 45.25065987],
                [142.6432197, 276.7472913, 37.539047],
                [142.4106286, 276.9015284, 40.53968072],
                [143.6423238, 277.4283058, 44.02384078],
                [144.0383778, 279.9186475, 47.11553193],
                [142.9863377, 279.3791154, 39.55077444],
                [144.0954178, 281.5402074, 37.66047668],
                [145.9964027, 281.4445289, 44.65503656],
                [145.2814106, 282.9467026, 43.07383207],
                [145.5164003, 284.3660139, 47.99842472],
                [145.4606927, 284.569582, 43.4608521],
                [147.3486316, 286.3730364, 44.98146161],
                [147.8053381, 288.0208851, 43.02129925],
                [147.8748837, 287.4346779, 40.42234767],
                [148.4108621, 289.0781608, 39.09166362],
                [149.6468485, 290.7732433, 43.6671315],
                [151.3869642, 290.270279, 43.55740303],
                [151.4428844, 292.6591352, 44.23809647],
                [152.7326312, 292.8814753, 43.68732765],
                [151.9974852, 294.3764297, 40.21626132],
                [153.0182535, 294.3550195, 46.80704735],
                [153.0175513, 295.8988859, 44.64836154],
                [153.2971517, 297.3655535, 43.17227517],
                [154.7717816, 298.2304517, 44.97442],
                [154.9612799, 299.2178757, 44.76656834],
                [155.2252263, 300.1460164, 45.01029886],
                [154.8347549, 300.8521549, 45.54168033],
                [156.5800691, 301.6459217, 42.49662738],
                [155.9855644, 302.8253253, 42.13642852],
                [155.9080211, 303.4481561, 45.69686101],
                [154.7456089, 304.7788436, 48.86864194],
                [156.2162099, 306.7431193, 50.19405306],
                [158.8418923, 306.5392107, 45.68727182],
                [160.0419775, 307.6577335, 42.17507531],
                [159.6928658, 308.2408351, 46.50564722],
                [158.6090458, 310.0281649, 45.54646805],
                [160.2759104, 310.4976617, 45.19662854],
                [162.33034, 312.721793, 50.33307076],
                [160.6251788, 313.2514313, 43.33336397],
                [162.5370215, 314.6776761, 40.70904805],
                [161.6521389, 314.9830545, 46.59369666],
                [160.8504578, 315.8802028, 37.2316138],
                [162.833324, 315.9317625, 45.51244341],
                [162.6103086, 318.5728379, 45.00096687],
                [164.3288899, 319.3298434, 41.22315112],
                [165.6827721, 319.8520309, 46.52771137],
                [164.5331276, 321.3714638, 41.52994471],
                [165.8096958, 322.8059253, 44.1283632],
                [166.7301524, 323.3402655, 47.87193653],
                [165.2621929, 323.1389099, 41.64222322],
                [165.86845, 324.4020467, 45.95863321],
                [166.2663108, 326.1236018, 46.6310431],
                [167.748973, 326.7806136, 49.38295518],
                [169.0722743, 328.4682883, 42.11847506],
                [168.5864507, 330.0869017, 42.72061148],
                [169.5936658, 329.5178573, 41.07016808],
                [170.2013583, 330.6302724, 46.56314141],
                [171.7660592, 332.3751828, 49.85288793],
                [170.7277147, 332.3920617, 40.22507821],
                [171.1676284, 334.6026359, 50.52123184],
                [170.3286002, 334.7417252, 46.14635817],
                [172.2390384, 335.6687997, 49.27168511],
                [172.801202, 336.7489947, 48.83809208],
                [174.1383303, 338.0578261, 47.71974196],
                [174.1078076, 338.4566917, 46.33993686],
                [173.0707055, 340.0874971, 45.97392728],
                [175.0149741, 340.9296195, 47.89020047],
                [173.5262489, 342.2234135, 54.26965144],
                [174.8096259, 343.5499576, 42.94451237],
                [177.3631166, 344.9731485, 46.21570193],
                [178.4858194, 345.7536106, 45.60143785],
                [175.610328, 345.6598323, 49.02558462],
                [176.8561781, 347.1601205, 44.9125587],
                [179.443353, 346.7760533, 51.88999955],
                [179.1456108, 349.6616815, 48.60527691],
                [179.7006448, 350.6542854, 50.09103957],
                [178.0209044, 351.9694853, 49.60398737],
                [182.1588849, 350.9919182, 45.47429159],
                [181.1342111, 353.0703574, 44.89127237],
                [180.8438696, 353.6809217, 49.37801026],
                [181.9530213, 354.7293466, 55.38740236],
                [180.8561193, 355.79333, 49.87131849],
                [182.2473994, 357.2107384, 49.58279763],
                [182.5295249, 357.9957494, 50.81278542],
                [182.8674238, 359.0788796, 46.32564896],
                [183.8491264, 359.6711246, 50.81347776],
                [185.8706672, 360.2790944, 41.15503434],
                [186.900414, 362.2661048, 52.16646155],
                [186.2469145, 362.1838823, 47.61224335],
                [184.7215862, 363.5368072, 54.90369074],
                [186.5237183, 364.5267827, 51.62836264],
                [187.2990259, 366.06209, 50.09010406],
                [189.0110683, 366.4237136, 50.80147607],
                [188.3656401, 368.8629451, 49.55062173],
                [189.2693026, 369.4413848, 46.36383936],
                [189.2354978, 369.2349175, 51.74870596],
                [190.6066681, 370.5712994, 50.68293185],
                [189.5098494, 372.1517727, 45.48870635],
                [191.4819634, 372.8720682, 51.26448975],
                [191.6739708, 373.4636161, 52.31027562],
                [190.9439482, 374.6237191, 50.23190305],
                [191.7887778, 375.4798787, 51.28329786],
                [192.4005678, 377.1267289, 56.57824476],
                [193.0255664, 378.1324117, 49.91092199],
                [195.1028827, 378.7544418, 46.69449937],
                [195.3644629, 381.1221051, 49.24807676],
                [195.8839904, 380.6777618, 49.49449503],
                [195.5746224, 381.8088638, 54.55762817],
                [196.2284318, 382.7784228, 56.22726832],
                [194.4611856, 383.7457091, 51.44099599],
                [196.775436, 385.0175742, 50.04759382],
                [197.0253338, 385.871714, 50.49909131],
                [196.6414509, 387.1103355, 52.94755907],
                [197.8325539, 387.4447729, 55.21265375],
                [199.2454405, 389.810864, 58.2614737],
                [199.4664844, 389.4033297, 57.46721085],
                [201.0124439, 390.7412025, 57.0742646],
                [200.3354222, 392.0890006, 56.28603505],
                [201.4530082, 392.6412844, 56.08860908],
                [200.1890634, 394.7406782, 59.2946252],
                [201.8436329, 395.0197914, 52.91899472],
                [201.1863919, 394.9200487, 53.48732203],
                [204.1929745, 397.0591228, 51.09651978],
                [203.8134586, 397.6412055, 54.12380536],
                [204.2997577, 398.5920085, 53.41563154],
                [204.354502, 400.0301851, 53.76910894],
                [204.2938933, 400.0098006, 55.18199024],
                [202.9817548, 402.8189672, 48.28995745],
                [206.7488163, 403.2709347, 49.66025525],
                [206.6520662, 403.7635868, 53.16942117],
                [206.706337, 405.3236848, 54.06029378],
                [208.2784144, 405.0010727, 52.69167638],
                [207.9358857, 407.4729301, 51.34644496],
                [208.645191, 407.9473673, 52.76380506],
                [209.5006216, 408.721601, 49.41741099],
                [208.8070787, 410.2105185, 55.47157875],
                [210.315957, 410.2506743, 50.15807133],
                [209.3034766, 412.5024793, 52.69217394],
                [211.7672482, 412.4592847, 60.2004219],
                [212.2643546, 413.3967647, 52.84065908],
                [212.0233839, 415.0378492, 55.7146884],
                [211.9570074, 415.7727338, 55.68601832],
                [214.3386896, 416.8743815, 49.23252318],
                [213.9902197, 417.6139829, 53.30745205],
                [213.0724856, 419.1932825, 55.0505883],
                [214.7162961, 418.9582065, 57.21887834],
                [215.9485831, 421.2770585, 58.39960966],
                [216.8930131, 421.0929402, 59.14587703],
                [216.9000389, 422.5125324, 61.65959779],
                [217.7295154, 423.3640877, 57.11358848],
                [216.8709934, 425.4071414, 49.07861383],
                [217.2045422, 425.2735266, 59.70678635],
                [217.3928103, 426.3156661, 56.90022452],
                [217.2673034, 428.1097358, 58.59075356],
                [219.0719427, 429.0477807, 57.83084609],
                [217.6368331, 430.5868804, 55.34445589],
                [218.4117405, 431.8897649, 60.20267762],
                [221.5743817, 432.1249158, 56.51110088],
                [220.0164222, 431.8592796, 53.67794368],
                [222.3673975, 434.2311864, 60.17590542],
                [220.4034264, 435.5356678, 59.14792016],
                [222.2548071, 435.341024, 58.00562979],
                [223.7345603, 436.9362072, 57.33717001],
                [224.5430844, 437.9720344, 59.45970912],
                [222.434522, 438.7670179, 57.37419128],
                [224.4722586, 440.760118, 58.17211017],
                [224.3376346, 440.7298199, 57.54507851],
                [224.5879234, 442.6650033, 57.97892047],
                [227.1046815, 442.8559041, 54.92290775],
                [225.9567242, 443.8355802, 62.05846174],
                [226.3740802, 444.520159, 54.47963419],
                [227.9550795, 446.4434188, 58.64068533],
                [228.7288882, 445.9833466, 59.17994676],
                [226.4019171, 447.5525348, 60.25561789],
                [229.068674, 449.0944034, 66.72309426],
                [229.0781528, 448.4052857, 60.66172389],
                [229.8730135, 450.9476315, 61.78658599],
                [230.339974, 451.341344, 57.90493874],
                [230.8665543, 452.402181, 60.70299103],
                [232.1389009, 453.7074331, 63.58450156],
                [230.6067023, 454.896686, 62.23978648],
                [232.3968262, 456.1948372, 61.78064025],
                [232.4404841, 456.6565249, 55.8201872],
                [234.1986788, 457.4556451, 65.82512703],
                [233.8977608, 460.0493813, 58.04283588],
                [234.2503623, 460.0154611, 61.77936125],
                [233.8469804, 461.0627001, 63.89527653],
                [237.0871363, 461.193794, 65.40968523],
                [235.190144, 462.3135016, 60.13134776],
                [238.2623381, 463.1788149, 61.24491574],
                [237.3329016, 465.4765071, 59.55926138],
                [235.9732813, 465.9058979, 64.13935229],
                [238.7038812, 466.2454404, 62.50374451],
                [239.1361374, 468.2601076, 61.75171819],
                [238.8371105, 468.4875622, 55.18527817],
                [240.0113954, 469.3644755, 65.07258653],
                [240.7653492, 471.0053354, 56.93270355],
                [240.660261, 472.1383836, 58.60128434],
                [241.8626276, 473.2168999, 60.24042431],
                [240.1618143, 474.9461334, 57.31137791],
                [242.3342942, 474.4959179, 63.1400804],
                [242.7607507, 476.0378378, 65.8870316],
                [243.7869334, 476.9194283, 55.08573557],
                [243.9338858, 478.0828128, 56.03709774],
                [243.2149554, 477.8549242, 65.50077429],
                [245.4747789, 478.7746617, 65.49545115],
                [244.3956103, 479.5573893, 64.7433395],
                [246.6066689, 480.9851159, 58.69295314],
                [245.8293764, 482.8866919, 62.14308665],
                [247.2564679, 484.3888379, 63.71269632],
                [247.7937162, 484.5790509, 62.56851712],
                [247.2643716, 484.9523281, 61.08496119],
                [249.9051735, 486.9166423, 60.92197809],
                [248.5624108, 488.169022, 61.88966941],
                [249.0109848, 489.4486468, 64.64292753],
                [247.6915071, 490.7726626, 57.46350819],
                [250.4485355, 491.1831783, 62.80134784],
                [250.675305, 492.3977657, 59.65348612],
                [252.3614761, 492.4718985, 64.66760281],
                [249.6940094, 493.7716707, 58.54494635],
                [251.8279364, 495.0555692, 65.24637886],
                [253.3939001, 495.9684086, 61.79047062],
                [253.7555695, 496.9530519, 62.35477801],
                [253.0849142, 497.5054957, 68.51712482],
                [255.1188327, 499.5793683, 60.7292712],
                [255.1427419, 499.3727025, 59.92753806],
                [256.2369481, 500.7184951, 63.74443398],
                [255.618888, 502.393057, 62.76761387],
                [256.1535134, 503.0470213, 62.33966196],
                [257.1566635, 503.6412649, 62.53874617],
                [257.154432, 505.6611575, 61.15538587],
                [257.2648036, 505.5174882, 62.85439156],
                [258.8164045, 506.7628506, 66.36610602],
                [259.4552734, 508.4476127, 61.77853986],
                [259.9735517, 509.5386514, 65.79948472],
                [258.5927984, 509.3277931, 64.06543116],
            ],
            columns = self.sec_names,
            index = self.date_idx
        )

        self.notionals = pd.DataFrame(
            [[1500, 2000, 500], [2000, 1500, 600]],
            columns = self.sec_names,
            index = self.date_idx[[0, 2]],
        )

        self.portfolio = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = 1000
        )
    
    def test_BS_regular(self):
        S0 = 10
        K = 11
        T = 1/12
        r = 0.0915
        q = 0
        vol = volm.Hist(portfolio = self.portfolio)

        bs = derivatives.BlackScholes(
            S0 = S0, K = K, T = T, r = r, q = q, vol = vol.vol
        )

        bs_call = bs.call
        bs_call_expected = 0.19

        self.assertAlmostEqual(
            bs_call, bs_call_expected, delta = 1e-2,
            msg = f'BlackScholes: wrong call price. Expected $ {bs_call_expected:.4f}, got $ {bs_call:.4f}' 
        )

        bs_put = bs.put
        bs_put_expected = 1.11

        self.assertAlmostEqual(
            bs_put, bs_put_expected, delta = 1e-2,
            msg = f'BlackScholes: wrong put price. Expected $ {bs_put_expected:.4f}, got $ {bs_put:.4f}' 
        )
    
    def test_BS_errors(self):
        params = dict(
            S0 = 10,
            K = 11,
            T = 1/12,
            r = 0.0915,
            q = 0,
            vol = volm.Hist(portfolio = self.portfolio).vol,
        )

        for param in params.keys():
            if param in ['q']:  # optional parameter
                continue
            params_minus1 = { k: v for k, v in params.items() if k != param }

            with self.assertRaises(
                TypeError,
                msg = f"BlackScholes: Must raise TypeError exception when missing '{param}' parameter."
            ):
                bs = derivatives.BlackScholes(**params_minus1)

    def test_BSP_value(self):
        bs = derivatives.BlackScholesPortfolio(
            portfolio = self.portfolio,
            volmodel = 'hist',
            base_date = pd.Timestamp('2022-05-11'),
            K = 245_000, r = 9.15 / 100, T = 1/12,
        )

        bs_call = bs.call
        bs_call_expected = 13250.12

        self.assertAlmostEqual(
            bs_call / 10000, bs_call_expected / 10000, delta = 1e-2,
            msg = f'BlackScholesPortfolio: wrong call price. Expected $ {bs_call_expected:.4f}, got $ {bs_call:.4f}' 
        )

        bs_put = bs.put
        bs_put_expected = 11401.11

        self.assertAlmostEqual(
            bs_put / 10000, bs_put_expected / 10000, delta = 1e-2,
            msg = f'BlackScholesPortfolio: wrong put price. Expected $ {bs_put_expected:.4f}, got $ {bs_put:.4f}' 
        )
    
    def test_BSP_errors(self):

        params = dict(
            portfolio = self.portfolio,
            base_date = pd.Timestamp('2022-05-11'),
            K = 245_000, r = 9.15 / 100, T = 1/12,
        )
        
        for param in params.keys():
            params_minus1 = { k: v for k, v in params.items() if k != param }

            with self.assertRaises(
                TypeError,
                msg = f"BlackScholesPortfolio: Must raise TypeError exception when missing '{param}' parameter."
            ):

                bs = derivatives.BlackScholesPortfolio(volmodel = 'hist', **params_minus1)